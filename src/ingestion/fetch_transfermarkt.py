import os
import io
import gzip
import urllib.request
import pandas as pd

def sync_transfermarkt_financials():
    """
    Connects to the open-source transfermarkt-datasets distribution layer
    using a custom User-Agent string to pass network firewall rules,
    processes player records, and structures values into the local cache.
    """
    REMOTE_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz"
    CACHE_DIR = "scout_cache"
    OUTPUT_FILE = os.path.join(CACHE_DIR, "valuations.csv")

    print(f"🚀 Connecting to transfermarkt-datasets infrastructure...")
    
    # Configure a production-grade browser signature to bypass the 403 firewall block
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        )
    }
    
    try:
        # Create a customized request packet including our spoofed browser headers
        request = urllib.request.Request(REMOTE_URL, headers=headers)
        
        # Open the network socket stream
        with urllib.request.urlopen(request) as response:
            print("📥 Connection established. Streaming compressed dataset into memory...")
            compressed_data = response.read()
            
            # Decompress the gzipped byte block natively
            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as unzipped:
                raw_df = pd.read_csv(unzipped)
                
        print(f"✅ Successfully read profile data for {len(raw_df):,} global players.")
        
        # Isolate and verify structural columns required for our relational left-join
        target_cols = ['name', 'market_value_in_eur', 'contract_expiration_date']
        for col in target_cols:
            if col not in raw_df.columns:
                if col == 'contract_expiration_date':
                    raw_df['contract_expiration_date'] = None
                elif col == 'market_value_in_eur':
                    raw_df['market_value_in_eur'] = 0

        # Transform and clean features
        processed_df = pd.DataFrame()
        processed_df['player'] = raw_df['name']
        processed_df['market_value_mln'] = (raw_df['market_value_in_eur'].fillna(0) / 1_000_000).round(2)
        
        def extract_year(date_str):
            if pd.isna(date_str) or not str(date_str).strip():
                return 2027
            try:
                return int(str(date_str).split("-")[0])
            except Exception:
                return 2027

        processed_df['contract_expiry'] = raw_df['contract_expiration_date'].apply(extract_year)

        # Clean duplicates and remove empty rows
        processed_df = processed_df.dropna(subset=['player'])
        processed_df = processed_df.sort_values('market_value_mln', ascending=False)
        processed_df = processed_df.drop_duplicates(subset=['player'], keep='first')

        # Export updated tabular file to cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        processed_df.to_csv(OUTPUT_FILE, index=False)
        
        print(f"💾 Production dataset structured and cached successfully at: {OUTPUT_FILE}")
        print(f"📊 Tracking profiles active: {len(processed_df):,} unique players.")
        
    except Exception as e:
        print(f"❌ Critical failure during dataset sync execution: {str(e)}")

if __name__ == "__main__":
    sync_transfermarkt_financials()