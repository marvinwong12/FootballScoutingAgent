import os
import sqlite3 
import pandas as pd
from typing import List, Dict, Optional
from src import normalize_name

class ScoutEngine:
    def __init__(self, cache_dir: str = None):
        """
        Initializes the analytical discovery query engine using the pre-compiled 
        SQLite table as a read-only memory asset.
        """
        # 1. Dynamically calculate the project root FIRST so it's always available
        current_file_path = os.path.abspath(__file__)          # src/engine/scout_engine.py
        src_dir = os.path.dirname(os.path.dirname(current_file_path)) # src/
        project_root = os.path.dirname(src_dir)                # smashing-monkeys/

        # 2. Assign the target directory based on input parameters
        if cache_dir is None:
            self.cache_dir = os.path.join(project_root, "data/scout_cache")
        else:
            self.cache_dir = cache_dir
            
        # 3. Secure the absolute path to the compiled SQLite database asset
        self.db_path = os.path.join(project_root, "data/scout_cache/scout_platform.db")
        
        self._df = None
        self._load_master_cache()

    def _load_master_cache(self):
        """Loads data cleanly into memory from SQLite once to provide high-speed execution profiles."""
        if os.path.exists(self.db_path):
            # Query the database and load the 'players' table into memory
            with sqlite3.connect(self.db_path) as conn:
                self._df = pd.read_sql_query("SELECT * FROM players", conn)
            print(f"[Engine Activated] Loaded warm master matrix cache from SQLite. Context Matrix Shape: {self._df.shape}")
        else:
            print(f"⚠️ Runtime Warning: SQLite database file not found at {self.db_path}.")
            print("Please run `src/ingestion/structured/compile_master.py` first to generate data assets.")
            self._df = pd.DataFrame()

        if not self._df.empty:
            self._df['match_name'] = self._df['player'].apply(normalize_name)

    def lookup_player(self, player_name: str) -> dict or str:
        """
        Retrieves a player's profile dictionary, using normalized matching to ignore 
        accents, casing, and spacing issues.
        """
        if self._df is None or self._df.empty:
            return "Database not loaded."

        from src.helper_functions import normalize_name
        clean_target = normalize_name(player_name)

        # 1. Primary Attempt: Exact match on the normalized name vector
        result = self._df[self._df['match_name'] == clean_target]
        
        # 2. Fallback Attempt: If exact normalized match fails, try a substring match 
        if result.empty:
            result = self._df[self._df['match_name'].str.contains(clean_target, na=False)]

        if result.empty:
            return f"No scout target found matching: {player_name}"

        # 3. Convert strictly the first matching row to a dictionary
        player_dict = result.iloc[0].to_dict()
        
        # 4. Scrub the internal helper key BEFORE returning
        player_dict.pop('match_name', None)
        
        return player_dict

    def discover_players(self, filters: dict, sort_by: str = None, ascending: bool = False, limit: int = 5) -> list or str:
        """
        Dynamic multi-metric query matrix filter matching future SQL query logic.
        Maps natural language filters to the normalized per90 underlying structural schema.
        """
        if self._df is None or self._df.empty:
            return "Error: Database cache not initialized or empty."
            
        df = self._df.copy()

        # 1. Positional Groupings
        if 'position' in filters and filters['position']:
            pos_query = filters['position'].lower().strip()
            
            if pos_query in ['df', 'defender', 'defenders', 'cb', 'lb', 'rb', 'd']:
                pos_targets = ['df', 'd']
            elif pos_query in ['mf', 'midfielder', 'midfielders', 'cm', 'dm', 'am', 'm']:
                pos_targets = ['mf', 'm']
            elif pos_query in ['fw', 'forward', 'forwards', 'st', 'striker', 'f']:
                pos_targets = ['fw', 'f']
            elif pos_query in ['gk', 'goalkeeper', 'goalkeepers']:
                pos_targets = ['gk']
            else:
                pos_targets = [pos_query]
        
            pos_col = 'position' if 'position' in df.columns else ('pos' if 'pos' in df.columns else None)
            if pos_col:
                pos_pattern = '|'.join(pos_targets)
                df = df[df[pos_col].astype(str).str.lower().str.contains(pos_pattern, na=False)]
        
        # League Canonical Mapping
        if 'league' in filters and filters['league']:
            league_query = str(filters['league']).lower().strip()
            if league_query in ['epl', 'premier league', 'english premier league', 'england premier league']:
                league_query = 'epl'
            elif league_query in ['la liga', 'laliga', 'primera division']:
                league_query = 'la liga'
            elif league_query in ['serie a', 'seriea']:
                league_query = 'serie a'
                
            if 'league' in df.columns:
                df = df[df['league'].astype(str).str.lower().str.strip() == league_query]
                
        # 2. Financial & Demographic Parameters
        if 'max_value_mln' in filters and filters['max_value_mln']:
            df = df[df['market_value_mln'].astype(float) <= float(filters['max_value_mln'])]
            
        if 'max_wage' in filters and filters['max_wage']:
            df = df[df['annual_wage_eur'].astype(float) <= float(filters['max_wage'])]

        if 'max_age' in filters and filters['max_age']:
            df = df[df['age'].astype(float) <= float(filters['max_age'])]

        if 'preferred_foot' in filters and filters['preferred_foot']:
            df = df[df['preferred_foot'].astype(str).str.lower() == str(filters['preferred_foot']).lower().strip()]

        if 'min_height' in filters and filters['min_height']:
            df = df[df['height_cm'].astype(float) >= float(filters['min_height'])]
            
        # 3. Dynamic Technical Metrics
        skip_keys = [
            'player', 'match_name', 'team', 'league', 'position', 'nation', 
            'preferred_foot', 'work_rate', 'player_traits',
            'market_value_mln', 'annual_wage_eur', 'contract_expiry',
            'matches', 'minutes', 'age', 'height_cm', 'weight_kg',
            'overall', 'potential', 'weak_foot', 'skill_moves', 
            'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic', 
            'mentality_vision', 'mentality_composure'
        ]
        
        for filter_key, filter_value in filters.items():
            if filter_key in skip_keys or filter_value is None:
                continue
                
            if filter_key.startswith('min_'):
                target_column = filter_key.replace('min_', '').lower().strip()
                if target_column not in df.columns and f"{target_column}_per90" in df.columns:
                    target_column = f"{target_column}_per90"
                if target_column in df.columns:
                    df = df[df[target_column].astype(float) >= float(filter_value)]

            elif filter_key.startswith('max_'):
                target_column = filter_key.replace('max_', '').lower().strip()
                if target_column not in df.columns and f"{target_column}_per90" in df.columns:
                    target_column = f"{target_column}_per90"
                if target_column in df.columns:
                    df = df[df[target_column].astype(float) <= float(filter_value)]
            
        if 'goals_per90' in df.columns and 'xg_per90' in df.columns:
            df['finishing_efficiency'] = df['goals_per90'] - df['xg_per90']

        # 4. Sorting Sequence Execution
        if sort_by:
            target_sort = sort_by.lower().strip()
            if target_sort in ['clinical', 'finishing', 'conversion']:
                target_sort = 'finishing_efficiency'
                ascending = False
            else:
                base_metric = target_sort.replace('_per90', '')
                if f"{base_metric}_per90" in df.columns:
                    target_sort = f"{base_metric}_per90"
                
            if target_sort in df.columns:
                df = df.sort_values(by=target_sort, ascending=ascending)
        else:
            fallback_sort = 'finishing_efficiency' if 'finishing_efficiency' in df.columns else ('xg_per90' if 'xg_per90' in df.columns else df.columns[0])
            df = df.sort_values(by=fallback_sort, ascending=False)
            
        clean_slice = df.head(limit).replace({pd.NA: None, float('nan'): None})
        return clean_slice.to_dict(orient="records")

    def get_player_percentiles(self, player_name: str, metrics: list[str]) -> Optional[dict[str, float]]:
        """
        Dynamically extracts raw stats and calculates real-time percentile rankings 
        against players in the SAME POSITION for accurate radar chart visualization.
        """
        if self._df is None or self._df.empty:
            return None
            
        from src.helper_functions import normalize_name
        clean_name = normalize_name(player_name)
        
        # 1. Find the target player
        result = self._df[self._df['player'] == clean_name]
        
        if result.empty:
            return None
            
        row = result.iloc[0]
        
        # 2. Extract their position and create a peer comparison group
        player_position = row.get('position')
        
        if pd.notna(player_position) and str(player_position).strip() != "":
            comparison_df = self._df[self._df['position'] == player_position]
            
            # Failsafe: If there are somehow less than 5 players in this position, 
            # fallback to comparing against the whole dataset to prevent math errors.
            if len(comparison_df) < 5:
                comparison_df = self._df
        else:
            # Fallback if the player has no assigned position
            comparison_df = self._df
            
        percentiles = {}
        
        # 3. Calculate position-adjusted percentiles
        for raw_metric in metrics:
            if raw_metric in self._df.columns:
                player_raw_val = row[raw_metric]
                
                if pd.isna(player_raw_val):
                    percentiles[raw_metric] = 50.0  # Average baseline for missing data
                else:
                    # DYNAMIC PERCENTILE MATH (vs. Positional Peers):
                    pct_rank = (comparison_df[raw_metric] <= player_raw_val).mean() * 100.0
                    percentiles[raw_metric] = float(pct_rank)
            else:
                percentiles[raw_metric] = 0.0 # Failsafe if metric name is wrong
                
        return percentiles