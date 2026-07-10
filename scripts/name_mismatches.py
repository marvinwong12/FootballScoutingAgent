import pandas as pd
import difflib
import unicodedata

# 1. Bring in your normalize_name function here
def normalize_name(name):
    if not isinstance(name, str): return str(name)
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

# 2. Load your raw CSVs (adjust paths as needed)
df_attack = pd.read_csv("./scout_cache/understat_attacking_big5_2025.csv") # Replace with actual path
df_defense = pd.read_csv("./scout_cache/fbref_defensive_big5_2526.csv")    # Replace with actual path

# Apply the basic normalizer
df_attack['match_name'] = df_attack['player'].apply(normalize_name)
df_defense['match_name'] = df_defense['player'].apply(normalize_name)

# 3. Find the "Orphans" (Players who exist in one list but not the other)
attack_names = set(df_attack['match_name'].dropna())
defense_names = set(df_defense['match_name'].dropna())

missing_from_defense = attack_names - defense_names
missing_from_attack = defense_names - attack_names

print(f"🔍 Found {len(missing_from_defense)} players only in Attacking data.")
print(f"🔍 Found {len(missing_from_attack)} players only in Defensive data.")

# 4. Use Fuzzy Matching to find likely pairs
print("\n--- COPY AND PASTE THESE INTO YOUR ALIAS DICTIONARY ---")
for atk_name in missing_from_defense:
    # Looks for matches in the defensive list that are at least 75% similar
    matches = difflib.get_close_matches(atk_name, missing_from_attack, n=1, cutoff=0.75)
    
    if matches:
        def_name = matches[0]
        # Prints perfectly formatted dictionary syntax!
        print(f'    "{atk_name}": "{def_name}",')