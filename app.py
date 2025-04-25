import pandas as pd
import streamlit as st
import plotly.express as px

# Load data
df = pd.read_csv("nfl_stats.csv")
df["game_date"] = pd.to_datetime(df["game_date"])

# Infer player positions from stats
position_guesses = []
for _, row in df.iterrows():
    if row["passing_yards"] > 0:
        position_guesses.append("QB")
    elif row["receiving_yards"] > row["rushing_yards"]:
        position_guesses.append("WR" if row["receiving_yards"] > 30 else "TE")
    else:
        position_guesses.append("RB")
df["position"] = position_guesses

# Derive opponent and home/away info
if "opponent" not in df.columns:
    if "game_string" in df.columns:
        df["opponent"] = df["game_string"].str.extract(r"vs (\w+)|@ (\w+)").bfill(axis=1).iloc[:, 0]
        df["home"] = df["game_string"].str.contains("vs")
    else:
        df["opponent"] = "Unknown"
        df["home"] = True

st.set_page_config(layout="wide")
st.title("📊 NFL Player Prop Tracker")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    selected_team = st.selectbox("Team", ["All"] + sorted(df["team"].unique()))
    selected_position = st.selectbox("Position", ["All", "QB", "RB", "WR", "TE"])
    selected_home = st.selectbox("Game Location", ["All", "Home", "Away"])

    filtered_df = df.copy()
    if selected_team != "All":
        filtered_df = filtered_df[filtered_df["team"] == selected_team]
    if selected_position != "All":
        filtered_df = filtered_df[filtered_df["position"] == selected_position]
    if selected_home != "All":
        home_bool = selected_home == "Home"
        filtered_df = filtered_df[filtered_df["home"] == home_bool]

    available_players = sorted(filtered_df["player"].unique())
    selected_player = st.selectbox("Player", available_players)

    stat_type = st.selectbox("Stat Type", [
        "Passing Yards", "Rushing Yards", "Receiving Yards",
        "Receptions", "Passing TDs", "Rushing TDs", "Receiving TDs"
    ])

    stat_column = {
        "Passing Yards": "passing_yards",
        "Rushing Yards": "rushing_yards",
        "Receiving Yards": "receiving_yards",
        "Receptions": "receptions",
        "Passing TDs": "passing_tds",
        "Rushing TDs": "rushing_tds",
        "Receiving TDs": "receiving_tds"
    }[stat_type]

    games_to_show = st.selectbox("Last N Games", [5, 10, 15, 20])
    prop_line = st.number_input(f"{stat_type} Prop Line", min_value=0.0, step=0.5)

# Filter and clean player data (before limiting to N games)
player_df = filtered_df[filtered_df["player"] == selected_player]
player_df = player_df.dropna(subset=[stat_column])
player_df = player_df.sort_values(by="game_date", ascending=False).head(games_to_show)
player_df = player_df.sort_values(by="game_date")  # chronological order

if player_df.empty:
    st.warning("No valid games with data found for that player.")
else:
    st.subheader(f"📅 Last {len(player_df)} Games – {selected_player}")
    st.dataframe(player_df[["game_date", "opponent", "home", stat_column]])

    # Hit rate
    over_hits = (player_df[stat_column] > prop_line).sum()
    hit_rate = (over_hits / len(player_df)) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Hits Over", f"{over_hits}/{len(player_df)}")
    col2.metric("Hit Rate", f"{hit_rate:.1f}%")
    col3.metric(f"Avg {stat_type}", f"{player_df[stat_column].mean():.1f}")

    # Build chart
    st.subheader("📈 Prop Chart")
    chart_df = player_df.copy()
    chart_df["game_label"] = chart_df.apply(
        lambda row: f"{'vs' if row['home'] else '@'} {row['opponent']}<br>{row['game_date'].strftime('%b %d')}", axis=1
    )
    chart_df["Result"] = chart_df[stat_column].apply(lambda x: "Over" if x > prop_line else "Under")
    category_order = chart_df["game_label"].tolist()

    fig = px.bar(
        chart_df,
        x="game_label",
        y=stat_column,
        color="Result",
        color_discrete_map={"Over": "green", "Under": "red"},
        title=f"{selected_player} – {stat_type} vs. Prop Line",
        category_orders={"game_label": category_order},
        hover_data=["opponent", "home"]
    )
    fig.add_hline(
        y=prop_line,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Prop Line: {prop_line}",
        annotation_position="top left"
    )
    fig.update_layout(
        xaxis_tickformat="%b %d",
        xaxis_tickangle=-30
    )

    st.plotly_chart(fig, use_container_width=True)

    # Download option
    st.download_button("📥 Download Player Data", player_df.to_csv(index=False), file_name="player_stats.csv")
