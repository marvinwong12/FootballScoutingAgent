import os
import soccerdata as sd
import pandas as pd
import time

def ingest_unified_defensive_data(season="2526"):
    print(f"--- STARTING UNIFIED DEFENSIVE INGESTION FOR THE {season} SEASON ---")
    
    storage_dir = "./data/scout_cache"
    os.makedirs(storage_dir, exist_ok=True)
    
    try:
        print("Fetching the 'Big 5 European Leagues Combined' dataset from FBref...")
        # A single call for all top 5 leagues
        fbref = sd.FBref(leagues="Big 5 European Leagues Combined", seasons=season, no_cache=True)
        
        player_df = fbref.read_player_season_stats(stat_type="misc")
        player_df = player_df.reset_index()
        
        # Flatten the MultiIndex tuple column headers
        flattened_cols = []
        for col in player_df.columns:
            if isinstance(col, tuple):
                if col[1] == '':
                    flattened_cols.append(col[0])
                else:
                    flattened_cols.append(f"{col[0]}_{col[1]}")
            else:
                flattened_cols.append(str(col))
        player_df.columns = flattened_cols
        
        # In the combined dataset, FBref usually stores the league name in 'comp' or 'stage'
        comp_col = 'comp' if 'comp' in player_df.columns else 'stage'
        
        # Verify the columns we want to slice
        cols_to_show = [
            'player', 'team', comp_col, 'minutes',
            'Performance_TklW', 'Performance_Int', 'Performance_Fls', 'Performance_CrdY'
        ]
        existing_cols = [c for c in cols_to_show if c in player_df.columns]
        
        # Process our custom hybrid metric
        if 'Performance_TklW' in player_df.columns and 'Performance_Int' in player_df.columns:
            player_df['ball_recoveries'] = player_df['Performance_TklW'] + player_df['Performance_Int']
            if 'ball_recoveries' not in existing_cols:
                existing_cols.append('ball_recoveries')
            player_df = player_df.sort_values(by="ball_recoveries", ascending=False)
            
        # Filter out players with low playing time
        if 'minutes' in player_df.columns:
            player_df = player_df[player_df['minutes'] >= 450]
            
        cleaned_df = player_df[existing_cols].round(2)
        
        # Rename the competition column simply to 'league' for your agents
        if comp_col in cleaned_df.columns:
            cleaned_df = cleaned_df.rename(columns={comp_col: 'league'})
        
        # Save ONE unified master file
        csv_path = os.path.join(storage_dir, f"fbref_defensive_big5_{season}.csv")
        cleaned_df.to_csv(csv_path, index=False)
        
        print(f"\n[SUCCESS] Exported {len(cleaned_df)} European players to ONE master file: {csv_path}")
            
    except Exception as e:
        print(f"[ERROR] Failed to ingest unified defensive data: {e}")

if __name__ == "__main__":
    ingest_unified_defensive_data(season="2526")