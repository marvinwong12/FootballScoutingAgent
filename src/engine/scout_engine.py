import os
import pandas as pd
import unicodedata

class ScoutEngine:
    def __init__(self, cache_dir=None):
        """
        Initializes the engine with an absolute path mapping to avoid FileNotFoundError.
        """
        if cache_dir is None:
            current_file_path = os.path.abspath(__file__) # src/engine/scout_engine.py
            src_dir = os.path.dirname(os.path.dirname(current_file_path)) # src/
            project_root = os.path.dirname(src_dir) # smashing-monkeys/
            self.cache_dir = os.path.join(project_root, "scout_cache")
        else:
            self.cache_dir = cache_dir
            
        print(f"[Engine Activation] Target data directory: {self.cache_dir}")

    def get_merged_scouting_profile(self, understat_season="2025", fbref_season="2526", min_minutes_threshold=90):
        """
        Loads the defensive, attacking, and unified financial files from the cache,
        merges them, and generates normalized per-90 metrics for accurate comparison.
        """
        attacking_file = os.path.join(self.cache_dir, f"understat_attacking_big5_{understat_season}.csv")
        defensive_file = os.path.join(self.cache_dir, f"fbref_defensive_big5_{fbref_season}.csv")
        valuation_file = os.path.join(self.cache_dir, "player_valuations_master.csv")
        
        if not os.path.exists(attacking_file) or not os.path.exists(defensive_file):
            return f"Error: Missing baseline data cache files."

        NAME_ALIASES = {
            "abdelkabir abqar": "abdel abqar", "abderrahmane rebbach": "abde rebbach",
            "abdessamad ezzalzouli": "abde ezzalzouli", "abduqodir khusanov": "abdukodir khusanov",
            "adam dzwigala": "adam dzwigaa", "adria alti": "adria altimira", "al musrati": "al-musrati",
            "albert grnbk": "albert grnbaek", "albert gudmundsson": "albert gumundsson",
            "alejandro catena": "alejandro balde", "alejandro jimenez": "alex jimenez",
            "alexander freeman": "alex freeman", "alexis claude maurice": "alexis claude-maurice",
            "ali youssef": "ali yousuf", "ali youssif": "ali yousuf", "altay bayindir": "altay bayndr",
            "amad diallo traore": "amad diallo", "ameen al dakhil": "ameen al-dakhil",
            "amir murillo": "michael amir murillo", "andrew robertson": "andy robertson",
            "anssumane fati": "ansu fati", "antonio martinez": "toni martinez",
            "arnaud kalimuendo muinga": "arnaud kalimuendo", "azz-eddine ounahi": "azzedine ounahi",
            "benjamin cremaschi": "ben cremaschi", "benoit badiashile mukinayi": "benoit badiashile",
            "berat gjimshiti": "berat djimsiti", "bertug yildirim": "bertug yldrm",
            "billal brahimi": "bilal brahimi", "borja sanchez": "borja sanchez laborde",
            "brad-hamilton mantsounga": "brad mantsounga", "cheick tidiane sabaly": "cheikh tidiane sabaly",
            "cheveyo mul": "cheveyo muy", "christian mawissa elebi": "christian mawissa",
            "dan ballard": "daniel ballard", "dani martinez": "daniel martinez", "dani vivian": "daniel vivian",
            "daniel cardenas": "dani cardenas", "daniel carvajal": "dani carvajal",
            "daniel mikolajewski": "daniel mikoajewski", "daniel semedo": "daniel xavier semedo",
            "darline yongwa": "darlin yongwa", "dayotchanculle upamecano": "dayot upamecano",
            "djordje petrovic": "ore petrovic", "dmytro bogdanov": "dmytro bohdanov", "eljif elmas": "elif elmas",
            "emile smith-rowe": "emile smith rowe", "emiliano buendia": "emi buendia",
            "enrico del prato": "enrico delprato", "eric junior dina ebimbe": "junior dina ebimbe",
            "eren sami dinkci": "eren dinkci", "etienne youte": "etienne youte kinkoue",
            "etta eyong": "karl etta eyong", "ezri konsa ngoyo": "ezri konsa",
            "faris moumbagna": "faris pemi moumbagna", "fernando lopez": "fer lopez",
            "filip jorgensen": "filip jrgensen", "fode toure": "fode ballo-toure", "fran perez": "francisco perez",
            "francesco pio esposito": "francesco esposito", "franco ezequiel carboni": "franco carboni",
            "frederik ronnow": "frederik rnnow", "gian-luca waldschmidt": "luca waldschmidt",
            "giorgi tsitaishvili": "heorhii tsitaishvili", "giovanni reyna": "gio reyna",
            "grant-leon ranos": "grant ranos", "hennes behrens": "hannes behrens",
            "hichem boudaoui": "hicham boudaoui", "hong hyun-seok": "hong hyunseok",
            "isak bergmann johannesson": "isak johannesson", "isak hansen-aaroen": "isak hansen-aaren",
            "iyenoma destiny udogie": "destiny udogie", "jamie bynoe-gittens": "jamie gittens",
            "jan ziolkowski": "jan ziokowski", "javi llabres": "javier llabres", "javi munoz": "javier munoz",
            "javier lopez": "javi lopez", "javier morcillo": "javi morcillo", "javier rodriguez": "javi rodriguez",
            "javier rueda": "javi rueda", "jaydon banel": "jaydon amauri banel",
            "jean-phillipe krasso": "jean-philippe krasso", "jesper lindstrom": "jesper lindstrm",
            "jesus santiago": "yellu santiago", "joakim maehle": "joakim mhle", "joao mario": "joao mario lopes",
            "job ochieng": "job ochieng'", "joel chima fujita": "joel fujita",
            "jones el abdellaoui": "jones el-abdellaoui", "jose gaya": "jose luis gaya", "joseph gomez": "joe gomez",
            "joseph n'duquidi": "joseph nduquidi", "josh acheampong": "joshua acheampong",
            "joshua vagnoman": "josha vagnoman", "juan cabal": "juan david cabal", "juan iglesias": "iglesias",
            "karl hein": "karl jakob hein", "kenan yildiz": "kenan yldz", "kephren thuram": "khephren thuram",
            "konan ndri": "konan n'dri", "konstantinos tsimikas": "kostas tsimikas", "kwon hyeok-kyu": "kwon hyeokkyu",
            "kylian mbappe-lottin": "kylian mbappe", "luc zogbe": "luck zogbe",
            "lucas gourna douath": "lucas gourna-douath", "luka djuric": "luka uric",
            "lukasz skorupski": "ukasz skorupski", "malthe hjholt": "malthe hojholt",
            "mama balde": "mama samba balde", "manuel fernandez": "manu fernandez",
            "manuel morlanes": "manu morlanes", "manuel sanchez": "manu sanchez", "marius louar": "marius louer",
            "martin bley": "martin nogoto bley", "martin odegaard": "martin degaard", "mat ryan": "mathew ryan",
            "mathys silistre": "mathys silestrie", "matias soule malvano": "matias soule",
            "matvey safonov": "matvei safonov", "matthew cash": "matty cash", "max weiss": "max wei",
            "maxi oyedele": "max oyedele", "maycon douglas cardozo": "maycon cardozo",
            "miguel sierra": "miguel angel sierra", "milan djuric": "milan uric", "mohamed ali-cho": "mohamed ali cho",
            "mohamed benoit-dao": "mohamed benoit dao", "mohammed amoura": "mohamed amoura",
            "morgan bokele": "morgan bokele mputu", "mousa al tamari": "musa al-taamari", "naif aguerd": "nayef aguerd",
            "ndary adopo": "michel ndary adopo", "nico paz": "nicolas paz", "nicolas": "nicolas paz",
            "nicolas kuhn": "nicolas-gerrit kuhn", "noam obougou": "noam obougou jacquet",
            "odisseas vlachodimos": "odysseas vlachodimos", "oladapo afolayan": "dapo afolayan",
            "oliver srensen": "oliver jensen", "orri oskarsson": "orri steinn oskarsson",
            "owen kouassi": "christ-owen kouassi", "pablo barrios rivas": "pablo barrios",
            "pape diop": "pape demba diop", "pape sarr": "pape matar sarr", "pereira lage": "mathias pereira lage",
            "philipp mwene": "phillipp mwene", "pierre-emile hjbjerg": "pierre hjbjerg",
            "przemyslaw frankowski": "przemysaw frankowski", "radoslaw majecki": "radosaw majecki",
            "rafael obrador": "rafel obrador", "rayan ait nouri": "rayan ait-nouri",
            "ruslan malinovskiy": "ruslan malinovskyi", "santiago cazorla": "santi cazorla",
            "santiago comesana": "santi comesana", "semih kilicsoy": "semih klcsoy", "sepe elye wahi": "elye wahi",
            "souleymane isaak toure": "souleymane toure", "stanis idumbo muzambo": "stanis idumbo",
            "stefan ortega moreno": "stefan ortega", "tai abed": "tay abed", "tanguy ndombele alvaro": "tanguy ndombele",
            "tasos douvikas": "anastasios douvikas", "terem igobor moffi": "terem moffi", "thiago pitarch": "thiago pinar",
            "thomas thiesson kristensen": "thomas kristensen", "unai vencedor": "unai vencedor paris",
            "valentino livramento": "tino livramento", "viktor tsygankov": "viktor tsyhankov",
            "vitalii mykolenko": "vitaliy mykolenko", "wedtoin ouedraogo": "latif ouedraogo",
            "william pacho": "willian pacho", "yann bisseck": "yann aurel bisseck",
            "yannick engelhardt": "yannik engelhardt", "yehor yarmolyuk": "yehor yarmoliuk", "yeremi pino": "yeremy pino",
        }
            
        df_attack = pd.read_csv(attacking_file)
        df_defense = pd.read_csv(defensive_file)

        def normalize_name(name):
            if not isinstance(name, str):
                return str(name)
            normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()
            if normalized in NAME_ALIASES:
                return NAME_ALIASES[normalized]
            return normalized

        # Normalize Column Header Casings Immediately
        df_attack.columns = df_attack.columns.str.lower()
        df_defense.columns = df_defense.columns.str.lower()
        
        # Prevent Suffix Collisions before Merging
        if 'team' in df_defense.columns:
            df_defense = df_defense.drop(columns=['team'])
        if 'league' in df_defense.columns:
            df_defense = df_defense.drop(columns=['league'])

        # Apply to both datasets
        df_attack['match_name'] = df_attack['player'].apply(normalize_name)
        df_defense['match_name'] = df_defense['player'].apply(normalize_name)

        # Deduplicate using the normalized names
        df_attack = df_attack.drop_duplicates(subset=['match_name'], keep='first')
        df_defense = df_defense.drop_duplicates(subset=['match_name'], keep='first')

        # Merge on the normalized name, keeping the display names intact
        master_df = pd.merge(df_attack, df_defense, on="match_name", how="outer", suffixes=('_atk', '_def'))

        # Consolidate the display name safely exactly once
        master_df['player'] = master_df['player_def'].fillna(master_df['player_atk'])
        
        # Drop the temporary split-name merge artifacts, but KEEP match_name for calculations
        master_df = master_df.drop(columns=['player_def', 'player_atk'], errors='ignore')

        # Clean up positions post-merge
        if 'position_x' in master_df.columns and 'position_y' in master_df.columns:
            master_df['position'] = master_df['position_x'].fillna(master_df['position_y']).fillna('UNKNOWN')
            master_df = master_df.drop(columns=['position_x', 'position_y'])
        elif 'position' in master_df.columns:
            master_df['position'] = master_df['position'].fillna('UNKNOWN')

        # Backfill all numeric performance columns with 0
        numeric_cols = master_df.select_dtypes(include=['number']).columns
        master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

        # Bring in financial data master file via Left Join
        if os.path.exists(valuation_file):
            val_df = pd.read_csv(valuation_file)
            val_df['match_name'] = val_df['player'].apply(normalize_name)
            val_df_deduped = val_df.drop_duplicates(subset=['match_name'], keep='first')
            
            # Combine financials safely on the existing match_name
            master_df = pd.merge(master_df, val_df_deduped.drop(columns=['player']), on='match_name', how='left')
            
            # Sanitize financial missing fallbacks
            master_df['annual_wage_eur'] = master_df.get('annual_wage_eur', pd.Series([0]*len(master_df))).fillna(0).astype(int)
            master_df['age'] = master_df.get('age', pd.Series([25]*len(master_df))).fillna(25).astype(int)
            master_df['market_value_mln'] = master_df.get('market_value_mln', pd.Series([0.0]*len(master_df))).fillna(0.0)
            master_df['nation'] = master_df.get('nation', pd.Series(['UNKNOWN']*len(master_df))).fillna('UNKNOWN')

        # 💡 ARCHITECTURE WIN: Save the FULL profile including financial parameters 
        # to the cached CSV file, keeping 'match_name' for O(1) runtime lookups.
        master_df.to_csv("./scout_cache/master_scouting_data.csv", index=False)

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
        """
        master_df = self.get_merged_scouting_profile()
        if isinstance(master_df, str):
            return master_df
            
        df = master_df.copy()

        print(f"DEBUG: Total players loaded into engine baseline: {len(df)}")
        
        # 1. Positional Filtering
        if 'position' in filters and filters['position']:
            pos_query = filters['position'].lower().strip()
            
            if pos_query in ['df', 'defender', 'defenders', 'cb', 'lb', 'rb']:
                pos_query = 'd'
            elif pos_query in ['mf', 'midfielder', 'midfielders', 'cm', 'dm', 'am']:
                pos_query = 'm'
            elif pos_query in ['fw', 'forward', 'forwards']:
                pos_query = 'f'
            elif pos_query in ['st', 'striker', 's']:
                pos_query = 's'
                
            pos_col = 'position' if 'position' in df.columns else ('pos' if 'pos' in df.columns else None)
            if pos_col:
                df = df[df[pos_col].str.lower().str.contains(pos_query, na=False)]
                
        # 2. Budget and Demographic Filtering 
        if 'max_value_mln' in filters and filters['max_value_mln']:
            df = df[df['market_value_mln'] <= float(filters['max_value_mln'])]
            
        if 'max_wage' in filters and filters['max_wage']:
            df = df[df['annual_wage_eur'] <= float(filters['max_wage'])]

        if 'max_age' in filters and filters['max_age']:
            df = df[df['age'] <= int(filters['max_age'])]
            
        # 3. Dynamic Performance Floors & Ceilings
        for filter_key, filter_value in filters.items():
            # 💡 THE FIX: Properly ignore all manually processed financial and demographic parameters
            if filter_key in ['position', 'max_value_mln', 'max_wage', 'max_age'] or filter_value is None:
                continue
                
            if filter_key.startswith('min_'):
                target_column = filter_key.replace('min_', '')
                if target_column in df.columns:
                    df = df[df[target_column].astype(float) >= float(filter_value)]
                    
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
    
    target_player = "Mohamed Salah"
    print(f"\n🔍 [TEST 1] Executing Atomic Lookup for: '{target_player}'...")
    profile = engine.lookup_player(target_player)
    
    if isinstance(profile, list) and len(profile) > 0:
        print(f"✅ Success! Found relational data row for {target_player}.\n")
        player_data = profile[0]
        print(f"   • Player Name:    {player_data.get('player')}")
        print(f"   • Performance xG: {player_data.get('xg_per90', 'N/A')} (From Understat)")
        print(f"   • Market Value:   €{player_data.get('market_value_mln', 'N/A')}M (From Transfermarkt)")
        print(f"   • Annual Wage:    €{player_data.get('annual_wage_eur', 'N/A'):,} (From Kaggle)")
        print(f"   • Age / Nation:   {player_data.get('age', 'N/A')} y/o | {player_data.get('nation', 'N/A')}")
        print(f"   • Contract Ends:  {player_data.get('contract_expiry', 'N/A')}")
    else:
        print(f"❌ Test Failed. Result: {profile}")

    print("\n" + "-" * 50)

    print("\n🎯 [TEST 2] Executing Discovery Filter Strategy...")
    print("   Criteria: Max €30M Value | Max €5M Wage | Sorted by highest goals")
    
    test_filters = {'max_value_mln': 30.0, 'max_annual_wage': 5_000_000}
    shortlist = engine.discover_players(filters=test_filters, sort_by='goals', ascending=False, limit=3)
    
    if isinstance(shortlist, list) and len(shortlist) > 0:
        print(f"✅ Success! Discovered {len(shortlist)} unique low-budget targets:\n")
        for idx, candidate in enumerate(shortlist, 1):
            pos_val = candidate.get('position', candidate.get('pos', 'N/A'))
            print(f"   [{idx}] {candidate.get('player')}")
            print(f"       - Position:     {pos_val}")
            print(f"       - Goals scored: {candidate.get('goals', 0)}")
            print(f"       - Value/Wage:   €{candidate.get('market_value_mln')}M / €{candidate.get('annual_wage_eur'):,}")
    else:
        print(f"⚠️ Query complete, but returned zero entries.")
        
    print("\n" + "=" * 60)