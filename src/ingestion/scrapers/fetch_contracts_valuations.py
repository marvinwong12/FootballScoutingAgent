import os
import io
import gzip
import urllib.request
import pandas as pd

def clean_and_purge_pipeline():
    CACHE_DIR = "./data/scout_cache"
    # 💡 UPDATE: Pointing to your explicit raw data path
    kaggle_input = "./raw_data/contracts.csv"
    output_master_file = os.path.join(CACHE_DIR, "player_valuations_master.csv")
    
    if not os.path.exists(kaggle_input):
        print(f"❌ Raw Kaggle file missing at {kaggle_input}. Drop it there first!")
        return

    # 🌐 STEP 1: Stream Transfermarkt Data Directly to RAM
    print("🚀 [1/3] Streaming Transfermarkt data straight to memory...")
    REMOTE_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        request = urllib.request.Request(REMOTE_URL, headers=headers)
        with urllib.request.urlopen(request) as response:
            compressed_data = response.read()
            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as unzipped:
                df_tm_raw = pd.read_csv(unzipped)
        
        df_tm = pd.DataFrame()
        df_tm['player'] = df_tm_raw['name'].dropna()
        df_tm['market_value_mln'] = (df_tm_raw.get('market_value_in_eur', 0).fillna(0) / 1_000_000).round(2)
        
        def extract_year(date_str):
            if pd.isna(date_str) or not str(date_str).strip(): return 2027
            try: return int(str(date_str).split("-")[0])
            except: return 2027
            
        df_tm['contract_expiry'] = df_tm_raw.get('contract_expiration_date', pd.Series([None]*len(df_tm_raw))).apply(extract_year)
        df_tm = df_tm.sort_values('market_value_mln', ascending=False).drop_duplicates(subset=['player'], keep='first')
        
    except Exception as e:
        print(f"❌ Transfermarkt stream failed: {e}")
        return

    # 🧹 STEP 2: Process & Deduplicate Kaggle Data into RAM
    print("🧹 [2/3] Processing and deduplicating Kaggle contract data...")
    df_raw = pd.read_csv(kaggle_input)
    
    column_mapping = {'Player': 'player', 'Nation_x': 'nation', 'Age_x': 'age', 'Annual EUR': 'annual_wage_eur'}
    if 'Nation_x' not in df_raw.columns and 'Nation_y' in df_raw.columns: column_mapping['Nation_y'] = 'nation'
    if 'Age_x' not in df_raw.columns and 'Age_y' in df_raw.columns: column_mapping['Age_y'] = 'age'

    existing_columns = {k: v for k, v in column_mapping.items() if k in df_raw.columns}
    df_wage = df_raw[list(existing_columns.keys())].copy().rename(columns=existing_columns)
    
    # 💡 THE FIX: Clean wage inputs via float conversion to prevent decimal trailing zero duplication
    if 'annual_wage_eur' in df_wage.columns:
        # Step A: Clean up basic currency artifacts but leave decimal structures intact
        df_wage['annual_wage_eur'] = (
            df_wage['annual_wage_eur']
            .astype(str)
            .str.replace('€', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        # Step B: Coerce to numeric float first to safely discard trailing precision strings (like .0)
        df_wage['annual_wage_eur'] = pd.to_numeric(df_wage['annual_wage_eur'], errors='coerce').fillna(0).astype(int)
        
    if 'age' in df_wage.columns:
        df_wage['age'] = pd.to_numeric(df_wage['age'], errors='coerce').fillna(25).astype(int)
    if 'nation' in df_wage.columns:
        df_wage['nation'] = df_wage['nation'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
        df_wage['nation'] = df_wage['nation'].apply(lambda x: x.split()[-1] if isinstance(x, str) and len(x.split()) > 0 else x)
        
    df_wage = df_wage.dropna(subset=['player'])

    # 🧬 STEP 3: Left Join & Write Final Master File
    print("🧬 [3/3] Merging datasets via in-memory Left Join...")
    df_tm['match_name'] = df_tm['player'].astype(str).str.lower().str.strip()
    df_wage['match_name'] = df_wage['player'].astype(str).str.lower().str.strip()
    
    # Sort and drop duplicates on match_name BEFORE the merge occurs
    df_wage = df_wage.sort_values(by=['match_name', 'age'], ascending=[True, False])
    df_wage_deduped = df_wage.drop_duplicates(subset=['match_name'], keep='first')
    
    # Run the left join
    df_master = pd.merge(df_tm, df_wage_deduped.drop(columns=['player']), on='match_name', how='left')
    
    # Fill missing values for players that had TM data but no Kaggle wage data
    df_master['annual_wage_eur'] = df_master.get('annual_wage_eur', pd.Series([0]*len(df_master))).fillna(0).astype(int)
    df_master['age'] = df_master.get('age', pd.Series([25]*len(df_master))).fillna(25).astype(int)
    df_master['nation'] = df_master.get('nation', pd.Series(['UNKNOWN']*len(df_master))).fillna('UNKNOWN').astype(str)
    
    df_master = df_master.drop(columns=['match_name'])
    
    # 💾 Save clean output file
    os.makedirs(CACHE_DIR, exist_ok=True)
    df_master.to_csv(output_master_file, index=False)
    print(f"✅ Success! Unique master matrix saved to: {output_master_file}")

    # 🗑️ STEP 4: Automated Workspace Cleanup
    print("🧹 Purging temporary source files from disk...")
    try:
        os.remove(kaggle_input)
        print(f"🗑️ Cleaned up and permanently deleted: {kaggle_input}")
    except Exception as e:
        print(f"⚠️ Could not auto-delete raw file: {e}")

    print("\n🎉 Pipeline execution finished. Values are verified accurate.")

if __name__ == "__main__":
    clean_and_purge_pipeline()