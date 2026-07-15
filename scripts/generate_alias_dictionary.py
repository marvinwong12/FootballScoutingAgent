import pandas as pd
import difflib

def generate_alias_lookup():
    master_path = "./scout_cache/master_scouting_data.csv"
    sofifa_path = "./scout_cache/sofifa_fc26_ratings.csv"

    print("🔍 Scanning datasets for unmatched player identities...\n")
    
    try:
        master_df = pd.read_csv(master_path)
        sofifa_df = pd.read_csv(sofifa_path)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    # 1. Identify players missing SoFIFA data
    missing_sofifa_mask = master_df['overall'].isna() | (master_df['overall'] == 0)
    unmatched_df = master_df[missing_sofifa_mask].copy()

    # 2. Filter out the noise
    # We only care about players who actually play or have value, to avoid 
    # cluttering the dictionary with thousands of irrelevant academy players.
    if 'minutes' in unmatched_df.columns:
        unmatched_df = unmatched_df[unmatched_df['minutes'] > 400]
    elif 'market_value_mln' in unmatched_df.columns:
        unmatched_df = unmatched_df[unmatched_df['market_value_mln'] > 2.0]
        
    # Sort by relevance so your biggest stars are at the top of the list
    if 'minutes' in unmatched_df.columns:
        unmatched_df = unmatched_df.sort_values(by='minutes', ascending=False)

    sofifa_names = sofifa_df['match_name'].dropna().unique().tolist()
    
    print("# ==========================================")
    print("# COPY AND PASTE THIS INTO SCOUT_ENGINE.PY")
    print("# ==========================================\n")
    print("MANUAL_ALIASES = {")
    
    # 3. Generate suggestions and build the dictionary syntax
    count = 0
    for _, row in unmatched_df.iterrows():
        m_name = str(row['match_name'])
        
        # Skip garbage rows
        if m_name == 'nan' or m_name.strip() == '':
            continue
            
        # Attempt to find fuzzy matches to help you out
        # We look for direct substrings first (e.g. "gabriel" inside "gabriel magalhaes")
        suggestions = [s for s in sofifa_names if m_name in s or s in m_name]
        
        # If no substring match, try difflib for typos
        if not suggestions:
            suggestions = difflib.get_close_matches(m_name, sofifa_names, n=3, cutoff=0.6)
            
        # Format the suggestions as a comment so you can easily pick the right one
        suggestion_str = f" # Suggestions: {', '.join(suggestions[:3])}" if suggestions else " # No obvious matches found"
        
        # Print the exact dictionary syntax
        print(f"    '{m_name}': '',{suggestion_str}")
        
        count += 1
        if count >= 50: # Cap it so it doesn't flood your terminal infinitely
            print("    # ... Run the script again with a higher cap to see more.")
            break
            
    print("}")
    print(f"\n✅ Found {len(unmatched_df)} significant players missing SoFIFA data.")

if __name__ == "__main__":
    generate_alias_lookup()