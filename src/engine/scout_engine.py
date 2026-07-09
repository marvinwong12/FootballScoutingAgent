import os
import pandas as pd

class ScoutEngine:
    def __init__(self, cache_dir=None):
        """
        Initializes the engine with an absolute path mapping to avoid FileNotFoundError.
        """
        if cache_dir is None:
            # Safely locate /Users/marvinwong/smashing-monkeys/scout_cache dynamically
            current_file_path = os.path.abspath(__file__) # src/engine/scout_engine.py
            src_dir = os.path.dirname(os.path.dirname(current_file_path)) # src/
            project_root = os.path.dirname(src_dir) # smashing-monkeys/
            self.cache_dir = os.path.join(project_root, "scout_cache")
        else:
            self.cache_dir = cache_dir
            
        print(f"[Engine Activation] Target data directory: {self.cache_dir}")

    def get_merged_scouting_profile(self, understat_season="2025", fbref_season="2526", min_minutes_threshold=90):
        """
        Loads the defensive, attacking, and financial files from the cache,
        merges them, and generates normalized per-90 metrics for accurate comparison.
        """
        attacking_file = os.path.join(self.cache_dir, f"understat_attacking_big5_{understat_season}.csv")
        defensive_file = os.path.join(self.cache_dir, f"fbref_defensive_big5_{fbref_season}.csv")
        valuation_file = os.path.join(self.cache_dir, "valuations.csv")
        
        if not os.path.exists(attacking_file) or not os.path.exists(defensive_file):
            return f"Error: Missing baseline data cache files."
            
        df_attack = pd.read_csv(attacking_file)
        df_defense = pd.read_csv(defensive_file)
        
        # 1. Normalize Column Header Casings Immediately
        df_attack.columns = df_attack.columns.str.lower()
        df_defense.columns = df_defense.columns.str.lower()
        
        # 2. Clean Name Disconnects
        for df in [df_attack, df_defense]:
            if 'player' in df.columns:
                df['player'] = df['player'].str.replace('Ghaly', '', case=False).str.strip()
        
        # 3. Prevent Suffix Collisions before Merging
        if 'team' in df_defense.columns:
            df_defense = df_defense.drop(columns=['team'])
        if 'league' in df_defense.columns:
            df_defense = df_defense.drop(columns=['league'])
            
        # 4. Core Relational Merge
        master_df = pd.merge(df_attack, df_defense, on="player", how="inner")
        
        # Remove duplication anomalies up front
        if 'goals' in master_df.columns:
            master_df = master_df.sort_values(by='goals', ascending=False)
        master_df = master_df.drop_duplicates(subset=['player'], keep='first')
        
        # 🛡️ Guardrail: Filter out players with tiny minute samples to prevent distorted data
        if 'minutes' in master_df.columns:
            master_df = master_df[master_df['minutes'].astype(float) >= min_minutes_threshold]
            
            # 📈 --- THE PER 90 NORMALIZATION MATRIX ---
            # Columns provided by user to normalize
            columns_to_normalize = [
                'performance_tklw', 'performance_int', 'performance_fls', 
                'performance_crdy', 'ball_recoveries', 'goals', 'np_goals', 
                'xg', 'np_xg', 'assists', 'xa', 'key_passes', 'shots', 
                'xg_chain', 'xg_buildup', 'yellow_cards', 'red_cards'
            ]
            
            # Compute rate metrics dynamically
            mins = master_df['minutes'].astype(float)
            for col in columns_to_normalize:
                if col in master_df.columns:
                    per90_col_name = f"{col}_per90"
                    # Safe division mask maps players with 0 minutes (if filtered out) to 0.0
                    master_df[per90_col_name] = ((master_df[col].astype(float) / mins) * 90.0).round(2)
        
        # 5. Relational Join Financial Valuations Layer
        if os.path.exists(valuation_file):
            val_df = pd.read_csv(valuation_file)
            val_df.columns = val_df.columns.str.lower()
            
            master_df = pd.merge(master_df, val_df, on="player", how="left")
            master_df['market_value_mln'] = master_df['market_value_mln'].fillna(10.0)
            master_df['contract_expiry'] = master_df['contract_expiry'].fillna(2027)
        else:
            master_df['market_value_mln'] = 10.0
            master_df['contract_expiry'] = 2027
            
        return master_df

    def lookup_player(self, player_name, understat_season="2025", fbref_season="2526"):
        """Atomic profile engine point-lookup tool."""
        master_df = self.get_merged_scouting_profile(understat_season, fbref_season)
        if isinstance(master_df, str): 
            return master_df 
        
        result = master_df[master_df['player'].str.contains(player_name, case=False, na=False)]
        if result.empty:
            return f"No scout target found matching: {player_name}"
            
        return result.to_dict(orient="records")

    def discover_players(self, filters: dict, sort_by: str = None, ascending: bool = False, limit: int = 5):
        """
        Dynamic multi-metric query matrix filter utilizing rate metrics.
        Natively processes any generic 'min_' or 'max_' prefix against dataframe columns.
        """
        master_df = self.get_merged_scouting_profile()
        if isinstance(master_df, str):
            return master_df
            
        df = master_df.copy()
        
        # 1. Positional Filtering
        if 'position' in filters and filters['position']:
            pos_query = filters['position'].lower()
            pos_col = 'position' if 'position' in df.columns else ('pos' if 'pos' in df.columns else None)
            if pos_col:
                df = df[df[pos_col].str.lower().str.contains(pos_query, na=False)]
                
        # 2. Financial Budget Filtering
        if 'max_value_mln' in filters and filters['max_value_mln']:
            df = df[df['market_value_mln'] <= float(filters['max_value_mln'])]
            
        # 3. 🛡️ FULLY DYNAMIC PERFORMANCE FLOORS & CEILINGS
        # Loops through any filter key starting with min_ or max_ and matches it to a dataframe column
        for filter_key, filter_value in filters.items():
            if filter_key in ['position', 'max_value_mln'] or filter_value is None:
                continue
                
            # Handle standard dynamic minimum conditions (e.g., 'min_key_passes_per90')
            if filter_key.startswith('min_'):
                target_column = filter_key.replace('min_', '')
                if target_column in df.columns:
                    df = df[df[target_column].astype(float) >= float(filter_value)]
                    
            # Handle standard dynamic maximum conditions (e.g., 'max_yellow_cards_per90')
            elif filter_key.startswith('max_'):
                target_column = filter_key.replace('max_', '')
                if target_column in df.columns:
                    df = df[df[target_column].astype(float) <= float(filter_value)]
            
        # 4. Sorting and Ranking
        if sort_by:
            target_sort = sort_by.lower().strip()
            if target_sort in ['goals', 'xg', 'assists'] and f"{target_sort}_per90" in df.columns:
                target_sort = f"{target_sort}_per90"
                
            if target_sort in df.columns:
                df = df.sort_values(by=target_sort, ascending=ascending)
        else:
            df = df.sort_values(by='xg_per90', ascending=False)
            
        return df.head(limit).to_dict(orient="records")


# ==========================================
# INFRASTRUCTURE VERIFICATION SUITE
# ==========================================
if __name__ == "__main__":
    import pprint
    engine = ScoutEngine()
    
    print("=" * 60)
    print("      SCOUT ENGINE INTEGRATION & MOVEMENT TEST")
    print("=" * 60)
    
    # TEST 1: Atomic Profile Lookup
    target_player = "Mohamed Salah"
    print(f"\n🔍 [TEST 1] Executing Atomic Lookup for: '{target_player}'...")
    profile = engine.lookup_player(target_player)
    
    if isinstance(profile, list) and len(profile) > 0:
        print(f"✅ Success! Found relational data row for {target_player}.\n")
        player_data = profile[0]
        print(f"   • Player Name:    {player_data.get('player')}")
        print(f"   • Performance xG: {player_data.get('xg_per90', 'N/A')} (From Understat)")
        print(f"   • Market Value:   €{player_data.get('market_value_mln', 'N/A')}M (From Transfermarkt)")
        print(f"   • Contract Ends:  {player_data.get('contract_expiry', 'N/A')}")
    else:
        print(f"❌ Test Failed. Result: {profile}")

    print("\n" + "-" * 50)

    # TEST 2: Discovery Engine Query
    print("\n🎯 [TEST 2] Executing Discovery Filter Strategy...")
    print("   Criteria: Max €30M Transfer Value | Sorted by highest goals")
    
    test_filters = {'max_value_mln': 30.0}
    shortlist = engine.discover_players(filters=test_filters, sort_by='goals', ascending=False, limit=3)
    
    if isinstance(shortlist, list) and len(shortlist) > 0:
        print(f"✅ Success! Discovered {len(shortlist)} unique low-budget targets:\n")
        for idx, candidate in enumerate(shortlist, 1):
            pos_val = candidate.get('position', candidate.get('pos', 'N/A'))
            print(f"   [{idx}] {candidate.get('player')}")
            print(f"       - Position:     {pos_val}")
            print(f"       - Goals scored: {candidate.get('goals', 0)}")
            print(f"       - Market Value: €{candidate.get('market_value_mln')}M")
    else:
        print(f"⚠️ Query complete, but returned zero entries.")
        
    print("\n" + "=" * 60)