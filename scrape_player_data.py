import pandas as pd
import time

# All starters across QB, RB, WR, TE with PFR IDs
starting_players = {
    # QBs
    "Patrick Mahomes": "MahoPa00",
    "Josh Allen": "AlleJo02",
    "Joe Burrow": "BurrJo00",
    "Jalen Hurts": "HurtJa00",
    "Justin Herbert": "HerbJu00",
    "Lamar Jackson": "JackLa00",
    "Tua Tagovailoa": "TagoTu00",
    "Trevor Lawrence": "LawrTr01",
    "C.J. Stroud": "StroCJ00",
    # RBs
    "Christian McCaffrey": "McCaCh01",
    "Derrick Henry": "HenrDe00",
    "Saquon Barkley": "BarkSa00",
    "Breece Hall": "HallBr00",
    "Bijan Robinson": "RobiBi00",
    # WRs
    "Justin Jefferson": "JeffJu00",
    "Tyreek Hill": "HillTy00",
    "Stefon Diggs": "DiggSt01",
    "CeeDee Lamb": "LambCe00",
    "A.J. Brown": "BrowAJ00",
    # TEs
    "Travis Kelce": "KelcTr00",
    "George Kittle": "KittGe00",
    "Mark Andrews": "AndrMa00",
    "T.J. Hockenson": "HockTJ00",
    "Dallas Goedert": "GoedDa00"
}

all_stats = []

for name, code in starting_players.items():
    for season_type, label in [("2024", "regular"), ("post", "postseason")]:
        url = f"https://www.pro-football-reference.com/players/{code[0]}/{code}/gamelog/{season_type}/"
        try:
            tables = pd.read_html(url, header=[0, 1])
            game_log = tables[0]
            game_log = game_log[game_log[('Unnamed: 3_level_0', 'Week')].notna()].copy()
            game_log.columns = ['_'.join(col).strip() for col in game_log.columns.values]

            date_col = [col for col in game_log.columns if 'Date' in col][0]

            game_log['game_date'] = pd.to_datetime(game_log[date_col], errors='coerce')
            game_log['player'] = name
            game_log['team'] = game_log['Team_Team'] if 'Team_Team' in game_log.columns else "Unknown"
            game_log['passing_yards'] = pd.to_numeric(game_log.get('Passing_Yds', 0), errors='coerce').fillna(0)
            game_log['rushing_yards'] = pd.to_numeric(game_log.get('Rushing_Yds', 0), errors='coerce').fillna(0)
            game_log['receiving_yards'] = pd.to_numeric(game_log.get('Receiving_Yds', 0), errors='coerce').fillna(0)
            game_log['receptions'] = pd.to_numeric(game_log.get('Receiving_Rec', 0), errors='coerce').fillna(0)
            game_log['passing_tds'] = pd.to_numeric(game_log.get('Passing_TD', 0), errors='coerce').fillna(0)
            game_log['rushing_tds'] = pd.to_numeric(game_log.get('Rushing_TD', 0), errors='coerce').fillna(0)
            game_log['receiving_tds'] = pd.to_numeric(game_log.get('Receiving_TD', 0), errors='coerce').fillna(0)

            cleaned = game_log[[
                'player', 'team', 'game_date',
                'passing_yards', 'rushing_yards', 'receiving_yards',
                'receptions', 'passing_tds', 'rushing_tds', 'receiving_tds'
            ]].copy()
            all_stats.append(cleaned)

            print(f"✅ Loaded {name} ({label})")
        except Exception as e:
            print(f"❌ Failed to load {name} ({label}): {e}")
        time.sleep(3)

if all_stats:
    final_df = pd.concat(all_stats).sort_values(by='game_date', ascending=False)
    final_df.to_csv("nfl_stats.csv", index=False)
    print("✅ All player stats saved to nfl_stats.csv")
else:
    print("⚠️ No data to save — check for scraping errors or rate limiting.")
