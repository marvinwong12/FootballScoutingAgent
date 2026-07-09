import os
import soccerdata as sd
import pandas as pd

def scout_defensive_gems():
    print("--- INITIALIZING SOCCERDATA FBREF API ---")
    fbref = sd.FBref(leagues="ENG-Premier League", seasons="2024")
    
    print("\n--- FETCHING MISC SEASON STATS FROM FBREF ---")
    try:
        player_df = fbref.read_player_season_stats(stat_type="misc")
        player_df = player_df.reset_index()
        
        # --- THE FIX: FLATTEN TUPLE COLUMNS CORRECTLY ---
        flattened_cols = []
        for col in player_df.columns:
            if isinstance(col, tuple):
                # If the second part is blank (like 'player', ''), keep just the first part ('player')
                if col[1] == '':
                    flattened_cols.append(col[0])
                else:
                    # If both parts have text (like 'Performance', 'TklW'), combine them
                    flattened_cols.append(f"{col[0]}_{col[1]}")
            else:
                flattened_cols.append(str(col))
                
        player_df.columns = flattened_cols
        # ------------------------------------------------
        
        print("\n--- PROCESSED COLUMNS ---")
        all_columns = list(player_df.columns)
        print(all_columns)
        print("-" * 40)
        
        # Match your targets using the newly flattened string keys
        cols_to_show = [
            'player', 'team', 'position', 'minutes',
            'Performance_TklW', 'Performance_Int', 'Performance_Fls', 'Performance_CrdY'
        ]
        
        # Verify columns exist in case names vary slightly by version
        cols_to_show = [c for c in cols_to_show if c in all_columns]
        
        # Calculate custom hybrid scouting metric
        if 'Performance_TklW' in player_df.columns and 'Performance_Int' in player_df.columns:
            player_df['ball_recoveries'] = player_df['Performance_TklW'] + player_df['Performance_Int']
            if 'ball_recoveries' not in cols_to_show:
                cols_to_show.append('ball_recoveries')
            
            top_defenders = player_df.sort_values(by="ball_recoveries", ascending=False)
        else:
            fallback_col = 'Performance_Int' if 'Performance_Int' in all_columns else all_columns[-1]
            top_defenders = player_df.sort_values(by=fallback_col, ascending=False)

        # Filter out low-minute options
        if 'minutes' in player_df.columns:
            top_defenders = top_defenders[top_defenders['minutes'] >= 450]

        print("\n--- TOP BALL WINNERS (SORTED BY TACKLES WON + INTERCEPTIONS) ---")
        print(top_defenders[cols_to_show].head(15).to_string(index=False))
        
        # Save output to cache
        storage_dir = "./scout_cache"
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        csv_path = os.path.join(storage_dir, "fbref_2025.csv")
        top_defenders[cols_to_show].to_csv(csv_path, index=False)
        print(f"\n[SUCCESS] Exported defensive dataset to: {csv_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scout_defensive_gems()