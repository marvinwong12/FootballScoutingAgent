import os
import soccerdata as sd
import pandas as pd

def test_understat_scrape():
    print("--- INITIALIZING SOCCERDATA UNDERSTAT API ---")
    # Using 2023 season data as a verified historical baseline
    us = sd.Understat(leagues="ENG-Premier League", seasons="2025")
    
    print("\n--- FETCHING ADVANCED SEASON STATS FROM UNDERSTAT ---")
    try:
        player_df = us.read_player_season_stats()
        player_df = player_df.reset_index()
        
        # Define our expanded scout metrics list using the exact columns you found!
        cols_to_show = [
            'player', 'team', 'position', 'matches', 'minutes', 
            'goals', 'np_goals', 'xg', 'np_xg', 
            'assists', 'xa', 'key_passes', 'shots', 
            'xg_chain', 'xg_buildup', 'yellow_cards', 'red_cards'
        ]
        
        # Sort by xG Chain to find the players most heavily involved in high-value attacks
        top_targets = player_df.sort_values(by="xg_chain", ascending=False)
        
        # Round the decimal values to 2 places so it is highly readable
        top_targets_clean = top_targets[cols_to_show].round(2)
        
        print("\n--- MASTER ATTACKING TARGETS (SORTED BY XG CHAIN) ---")
        print(top_targets_clean.head(15).to_string(index=False))
        
        # --- EXPORT FOR MULTI-AGENT USE ---
        # Create a local cache directory if it doesn't exist
        storage_dir = "./scout_cache"
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        csv_path = os.path.join(storage_dir, "understat_2025.csv")
        top_targets_clean.to_csv(csv_path, index=False)
        print(f"\n[SUCCESS] Exported all {len(player_df)} player files to: {csv_path}")
        print("Your multi-agent system can now parse this CSV instantly!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_understat_scrape()