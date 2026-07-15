import os
import unicodedata
import pandas as pd

def normalize_name(name: str) -> str:
    """Instantly reduces any player name variation to a clean search key."""
    if not isinstance(name, str): 
        return str(name)
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def process_sofifa_dataset(raw_filepath: str, output_filepath: str):
    print(f"Loading raw SoFIFA dataset from {raw_filepath}...")
    
    try:
        df_raw = pd.read_csv(raw_filepath, low_memory=False)
    except FileNotFoundError:
        print(f"Error: Could not find the file at {raw_filepath}")
        return

    # ==========================================
    # 🌍 LEAGUE PREPROCESSING FILTER (TOP 5)
    # ==========================================
    if 'league_name' in df_raw.columns:
        print("Filtering for Top 5 European Leagues (Premier League, Bundesliga, La Liga, Serie A, Ligue 1)...")
        
        # Define allowed leagues (lowercased for strict, case-insensitive comparison)
        allowed_leagues = [
            "premier league", 
            "bundesliga", 
            "la liga", 
            "serie a",   # Fixed standard dataset spelling
            "seria a",   # Safety fallback for manual data alterations
            "ligue 1"
        ]
        
        # Standardize strings dynamically to match lower elements
        df_raw['league_name_lower'] = df_raw['league_name'].astype(str).str.lower().str.strip()
        
        # Apply the filter mask
        df_raw = df_raw[df_raw['league_name_lower'].isin(allowed_leagues)]
        
        # Drop the temporary column
        df_raw = df_raw.drop(columns=['league_name_lower'])
        print(f"Filtered baseline size down to {len(df_raw)} records remaining.")
    else:
        print("⚠️ Warning: 'league_name' column not found in raw data. Skipping step.")

    # ==========================================
    # CORE PIPELINE & DATA CLEANING
    # ==========================================
    print("Generating normalized match keys...")
    df_raw['match_name'] = df_raw['long_name'].apply(normalize_name)

    # Define the precise, non-redundant columns to retain
    columns_to_keep = [
        'match_name', 
        'overall', 
        'potential', 
        'height_cm', 
        'weight_kg', 
        'preferred_foot', 
        'weak_foot', 
        'skill_moves', 
        'work_rate',
        'pace', 
        'shooting', 
        'passing', 
        'dribbling', 
        'defending', 
        'physic',
        'mentality_vision', 
        'mentality_composure',
        'player_traits'
    ]

    # Filter to only keep columns that actually exist in the CSV
    available_columns = [col for col in columns_to_keep if col in df_raw.columns]
    df_clean = df_raw[available_columns]

    # Deduplicate entries, retaining the version with the highest overall rating
    df_clean = df_clean.sort_values('overall', ascending=False)
    df_clean = df_clean.drop_duplicates(subset=['match_name'], keep='first')

    # Save cleanly back to our project cache directory
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    df_clean.to_csv(output_filepath, index=False)
    
    print(f"✅ Success! Cleaned dataset saved to {output_filepath}")
    print(f"Total players processed: {len(df_clean)}")
    print(f"Columns retained: {len(df_clean.columns)}")

if __name__ == "__main__":
    RAW_FILE_PATH = "./raw_data/FC26_data.csv" 
    CLEAN_FILE_PATH = "./data/scout_cache/sofifa_fc26_ratings.csv"
    
    process_sofifa_dataset(RAW_FILE_PATH, CLEAN_FILE_PATH)