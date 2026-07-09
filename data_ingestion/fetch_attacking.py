import os
import soccerdata as sd
import pandas as pd
import time

def ingest_unified_attacking_data(season="2025"):
    print(f"--- STARTING UNIFIED ATTACKING INGESTION FOR THE {season} SEASON ---")
    
    leagues = {
        "EPL": "ENG-Premier League",
        "LaLiga": "ESP-La Liga",
        "Bundesliga": "GER-Bundesliga",
        "SerieA": "ITA-Serie A",
        "Ligue1": "FRA-Ligue 1"
    }
    
    storage_dir = "./scout_cache"
    os.makedirs(storage_dir, exist_ok=True)
    
    cols_to_show = [
        'player', 'team', 'position', 'matches', 'minutes', 
        'goals', 'np_goals', 'xg', 'np_xg', 
        'assists', 'xa', 'key_passes', 'shots', 
        'xg_chain', 'xg_buildup', 'yellow_cards', 'red_cards'
    ]
    
    # This list will hold the DataFrames for each league temporarily
    all_league_dfs = []

    for label, league_id in leagues.items():
        print(f"\nInitializing Understat wrapper for {label}...")
        try:
            us = sd.Understat(leagues=league_id, seasons=season)
            player_df = us.read_player_season_stats()
            player_df = player_df.reset_index()
            
            existing_cols = [c for c in cols_to_show if c in player_df.columns]
            cleaned_df = player_df[existing_cols].copy()
            
            # Add the league identifier column
            cleaned_df.insert(2, 'league', label)
            
            # Append this league's data to our master list
            all_league_dfs.append(cleaned_df)
            print(f"[SUCCESS] Scraped {len(cleaned_df)} players from {label}")
            
            time.sleep(2.0)
            
        except Exception as e:
            print(f"[ERROR] Failed to ingest data for {label}: {e}")
            
    # --- COMBINE AND EXPORT TO ONE FILE ---
    if all_league_dfs:
        print("\nCombining all leagues into one master attacking dataset...")
        master_attacking_df = pd.concat(all_league_dfs, ignore_index=True)
        
        # Sort globally by xG chain and round numbers
        if 'xg_chain' in master_attacking_df.columns:
            master_attacking_df = master_attacking_df.sort_values(by="xg_chain", ascending=False)
        master_attacking_df = master_attacking_df.round(2)
        
        csv_path = os.path.join(storage_dir, f"understat_attacking_big5_{season}.csv")
        master_attacking_df.to_csv(csv_path, index=False)
        print(f"[SUCCESS] Exported {len(master_attacking_df)} total players to ONE master file: {csv_path}")
    else:
        print("[ERROR] No league data was collected. Master file not created.")

if __name__ == "__main__":
    ingest_unified_attacking_data(season="2025")