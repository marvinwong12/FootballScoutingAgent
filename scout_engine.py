import os
import pandas as pd

class ScoutEngine:
    def __init__(self, cache_dir="./scout_cache"):
        self.cache_dir = cache_dir

    def get_merged_scouting_profile(self, understat_season="2025", fbref_season="2526"):
        """
        Loads the defensive and attacking unified big5 files from the cache,
        merges them on the player name, and returns a master profile.
        """
        # Correct the file names to match the unified Big 5 outputs
        attacking_file = os.path.join(self.cache_dir, f"understat_attacking_big5_{understat_season}.csv")
        defensive_file = os.path.join(self.cache_dir, f"fbref_defensive_big5_{fbref_season}.csv")
        
        if not os.path.exists(attacking_file) or not os.path.exists(defensive_file):
            return f"Error: Missing baseline data cache files.\nLooking for:\n- {attacking_file}\n- {defensive_file}\nPlease run your ingestion scripts first."
            
        # Read independent datasets
        df_attack = pd.read_csv(attacking_file)
        df_defense = pd.read_csv(defensive_file)
        
        # Strip team from the defensive side to avoid 'team_x' and 'team_y' name collisions.
        # Understat will serve as our primary source for team and league data.
        if 'team' in df_defense.columns:
            df_defense = df_defense.drop(columns=['team'])
            
        # Strip any extra structural league/comp column if FBref included it, 
        # so we don't duplicate it against Understat's 'league' column.
        if 'league' in df_defense.columns:
            df_defense = df_defense.drop(columns=['league'])
            
        # Merge exactly on the shared 'player' column string match
        master_df = pd.merge(df_attack, df_defense, on="player", how="inner")
        return master_df

    def lookup_player(self, player_name, understat_season="2025", fbref_season="2526"):
        """A clean atomic tool for an AI agent to inspect a single player profile"""
        master_df = self.get_merged_scouting_profile(understat_season, fbref_season)
        if isinstance(master_df, str): 
            return master_df # Returns the missing file error message string
        
        # Search for the player name (case insensitive partial match)
        result = master_df[master_df['player'].str.contains(player_name, case=False, na=False)]
        if result.empty:
            return f"No scout target found matching: {player_name}"
            
        return result.to_dict(orient="records")

# Test execution
if __name__ == "__main__":
    engine = ScoutEngine()
    print("--- MERGING DATA LAYERS ---")
    
    # Try searching for a hybrid profile in the 25/26 database
    player_profile = engine.lookup_player("Mohamed Salah")
    
    import pprint
    pprint.pprint(player_profile)