from src.engine.scout_engine import ScoutEngine

def main():
    engine = ScoutEngine()
    df = engine._df
    
    if df is None or df.empty:
        print("Dataset is empty.")
        return

    # Search the match_name column for anything containing 'mbappe' (case-insensitive)
    print("Searching for 'mbappe'...")
    mbappe_matches = df[df['match_name'].str.lower().str.contains('mbappe', na=False)]
    
    if not mbappe_matches.empty:
        print("✅ Found him! Here is EXACTLY how he is stored in your database:")
        print(mbappe_matches['match_name'].tolist())
    else:
        print("❌ Mbappe is NOT in this dataset! Let's try finding 'haaland' instead...")
        haaland_matches = df[df['match_name'].str.lower().str.contains('haaland', na=False)]
        print(haaland_matches['match_name'].tolist())

if __name__ == "__main__":
    main()