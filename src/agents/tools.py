import unicodedata
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from langchain.tools import tool
from src.engine.scout_engine import ScoutEngine 

# Instantiate the global engine instance that your tools use
_engine = ScoutEngine()

# ==========================================
# UNIVERSAL HELPER (Fast Lookup)
# ==========================================
def normalize_name(name: str) -> str:
    """Instantly reduces any player name variation to a clean search key."""
    if not isinstance(name, str): 
        return str(name)
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()


# ==========================================
# 1. DATA ENGINE TOOLS (Structured Analytics)
# ==========================================
@tool
def search_player_tactical_tool(player_name: str) -> str:
    """
    Searches the database for a specific player's statistical profile.
    """
    try:
        # Load the database (which now has the pre-computed 'match_name' column)
        df = pd.read_csv("./scout_cache/master_scouting_data.csv")
        
        # Normalize ONLY the LLM's input (instantaneous)
        clean_search_name = normalize_name(player_name)
        
        # Direct lookup! No expensive apply() functions needed.
        player_data = df[df['match_name'] == clean_search_name]
        
        if player_data.empty:
            return f"Could not find any data for {player_name}."
            
        # Clean up the output so the LLM doesn't get confused by duplicate name columns
        player_data = player_data.drop(columns=['match_name'])
        
        return player_data.to_json(orient="records")
        
    except Exception as e:
        return f"Error reading database: {str(e)}"


@tool
def discovery_scout_tool(
    *,
    position: str = None, 
    max_value_millions: float = None, 
    max_wage: float = None,  
    max_age: int = None,
    target_metric: str = None, 
    min_metric_value: float = None,
    sort_by_metric: str = "xg_per90",
    highest_first: bool = True
) -> str:
    """
    Scans the global database to discover players matching budget, role, age, and wage limits.

    Args:
        position (str): Target role on the pitch (e.g., 'FW', 'MF', 'DF').
        max_value_millions (float): Maximum transfer market budget ceiling in millions (e.g., 30.0).
        max_wage (float): Maximum annual wage budget in Euros (e.g., 4000000).
        max_age (int): Maximum player age ceiling (e.g., 25).
    """
    query_filters = {}
    if position: query_filters['position'] = position
    if max_value_millions: query_filters['max_value_mln'] = max_value_millions
    if max_wage: query_filters['max_wage'] = max_wage
    if max_age: query_filters['max_age'] = max_age
        
    # Mapping custom filters dynamically to our unified engine keys
    if target_metric and min_metric_value is not None:
        metric_key = target_metric.lower().strip()
        
        # Financial and core demographic markers do not get a suffix
        exempt_base_columns = ['market_value_mln', 'contract_expiry', 'annual_wage_eur', 'weekly_wage_eur', 'age']
        if not metric_key.endswith('_per90') and metric_key not in exempt_base_columns:
            metric_key = f"{metric_key}_per90"
            
        if 'goals_per90' in metric_key:
            query_filters['min_goals_per90'] = min_metric_value
        elif 'xg_per90' in metric_key:
            query_filters['min_xg_per90'] = min_metric_value
        else:
            query_filters[f"min_{metric_key}"] = min_metric_value

    # Enforce clean sorting metrics
    sort_column = sort_by_metric.lower().strip()
    exempt_sort_columns = ['market_value_mln', 'contract_expiry', 'minutes', 'annual_wage_eur', 'age']
    
    if not sort_column.endswith('_per90') and sort_column not in exempt_sort_columns:
        sort_column = f"{sort_column}_per90"

    # Query the engine. Note: The engine should be returning data with the 
    # 'match_name' column dropped or kept for display, but lookup is handled via the underlying DataFrame.
    matches = _engine.discover_players(
        filters=query_filters, 
        sort_by=sort_column, 
        ascending=(not highest_first), 
        limit=3
    )
    
    # LOOP BREAKER: Defensively halt recursive hallucination loops if zero data is found
    if not matches or isinstance(matches, str) or len(matches) == 0:
        return (
            "CRITICAL: No players matching your exact tactical or financial constraints "
            "were found in the database. Do not attempt this query again. Report directly "
            "to the user that zero players matched these specific limits."
        )
        
    return str(matches)


# ==========================================
# 2. BEHAVIORAL ANALYST TOOLS (The RAG Component)
# ==========================================
@tool
def query_player_narrative_tool(player_name: str) -> str:
    """
    Retrieves qualitative scouting insights, medical/injury history, 
    character assessments, and tactical profiles for a specific football player.
    Always query this tool to check for background risks after finding potential targets.
    """
    try:
        # Connect to the local database
        chroma_client = chromadb.PersistentClient(path="./scout_cache/vector_db")
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = chroma_client.get_collection(name="player_narratives", embedding_function=embedding_fn)
        
        # THE ARCHITECTURE FIX: One instant normalization on the incoming target parameter
        clean_search_name = normalize_name(player_name)
        
        # Query matching the exact pre-calculated identity key stored during ingestion
        results = collection.get(
            where={"player_match_name": clean_search_name}
        )
        
        if results and results['documents'] and len(results['documents']) > 0:
            return f"--- QUALITATIVE SCOUTING REPORT FOR {player_name.upper()} ---\n{results['documents'][0]}"
            
        # Semantic fallback: If metadata misses, evaluate similarity against the pre-compiled lookup key
        semantic_results = collection.query(
            query_texts=[f"injury history tactical character profile for {clean_search_name}"],
            n_results=1
        )
        if semantic_results and semantic_results['documents'] and len(semantic_results['documents'][0]) > 0:
            return f"--- RELATED NARRATIVE MATCH FOR {player_name.upper()} ---\n{semantic_results['documents'][0][0]}"
            
        return f"No qualitative injury or character reports found in local text database for '{player_name}'."
        
    except Exception as e:
        return f"Error querying local vector storage: {str(e)}"


# ==========================================
# TOOL REGISTRATION MATRIX
# ==========================================
SCOUT_TOOLS = [
    search_player_tactical_tool,
    discovery_scout_tool,
    query_player_narrative_tool
]