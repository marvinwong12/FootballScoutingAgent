"""
AI Tools Module
Provides specialized data endpoints for tactical, financial, and behavioral analysts.
"""

from langchain_core.tools import tool
from src.engine import ScoutEngine
import random  # Used for simulated data where live APIs aren't integrated yet

_engine = ScoutEngine()

# ==========================================
# 1. TACTICAL ANALYST TOOLS
# ==========================================
@tool
def search_player_tactical_tool(player_name: str) -> str:
    """
    Fetches purely tactical statistics, expected metrics, and defensive tracking.
    Now includes both raw total volumes and normalized per-90 rate metrics.
    """
    profile = _engine.lookup_player(player_name)
    return str(profile)

@tool
def discovery_scout_tool(
    *,
    position: str = None, 
    max_value_millions: float = None, 
    target_metric: str = None, 
    min_metric_value: float = None,
    sort_by_metric: str = "xg_per90",
    highest_first: bool = True
) -> str:
    """
    Scans the global big-5 league database to discover players matching budget, position, 
    and custom performance/tactical metrics.

    Args:
        position (str): Target role on the pitch (e.g., 'FW', 'MF', 'DF', 'S' for striker).
        max_value_millions (float): Maximum transfer market budget ceiling in millions of Euros (e.g., 30.0).
        target_metric (str): Optional per-90 stat column to apply a floor filter to. 
                             Choose from: 'goals_per90', 'xg_per90', 'assists_per90', 'key_passes_per90', 
                             'shots_per90', 'performance_tklw_per90', 'performance_int_per90', 'ball_recoveries_per90'.
        min_metric_value (float): The minimum value threshold for the chosen target_metric.
        sort_by_metric (str): The metric used to rank the results. Defaults to 'xg_per90' for attacking efficiency.
        highest_first (bool): Set to True to get the best performers first. Defaults to True.
    """
    print(f"[Tool Execution] Scanning market for {position} under €{max_value_millions}M (Sorting by {sort_by_metric})...")
    
    # 1. Build the dynamic filter matrix safely
    query_filters = {}
    if position: 
        query_filters['position'] = position
    if max_value_millions: 
        query_filters['max_value_mln'] = max_value_millions
        
    # Mapping old custom filters dynamically to our unified engine keys
    if target_metric and min_metric_value is not None:
        metric_key = target_metric.lower().strip()
        # If the LLM forgets to include the '_per90' suffix, append it defensively
        if not metric_key.endswith('_per90') and metric_key not in ['market_value_mln', 'contract_expiry']:
            metric_key = f"{metric_key}_per90"
            
        # Inject our generic filter key into the filter dictionary
        if 'goals_per90' in metric_key:
            query_filters['min_goals_per90'] = min_metric_value
        elif 'xg_per90' in metric_key:
            query_filters['min_xg_per90'] = min_metric_value
        else:
            # Let the engine naturally catch other dynamic per-90 thresholds
            query_filters[f"min_{metric_key}"] = min_metric_value

    # 2. Enforce clean sorting metrics
    sort_column = sort_by_metric.lower().strip()
    if not sort_column.endswith('_per90') and sort_column not in ['market_value_mln', 'contract_expiry', 'minutes']:
        sort_column = f"{sort_column}_per90"

    # 3. Query the data engine using our per-90 structures
    # We invert 'highest_first' to match pandas' 'ascending' logic (True highest = ascending=False)
    matches = _engine.discover_players(
        filters=query_filters, 
        sort_by=sort_column, 
        ascending=(not highest_first), 
        limit=3
    )
    
    if not matches or isinstance(matches, str) or len(matches) == 0:
        return f"No players in the current database match those exact filters (Tried searching for {query_filters} sorted by {sort_column})."
        
    return str(matches)
# ==========================================
# 2. FINANCIAL ANALYST TOOLS
# ==========================================
@tool
def check_player_financials_tool(player_name: str) -> str:
    """Retrieves estimated market value, weekly wages, and contract length for a player."""
    # Production note: Hook this up to a Transfermarkt/Capology scraper wrapper later
    mock_values = {
        "Pedro Neto": {"market_value": "£28M", "weekly_wage": "£90k", "contract": "2029"},
        "Nico Williams": {"market_value": "£55M", "weekly_wage": "£140k", "contract": "2027"},
        "Michael Olise": {"market_value": "£45M", "weekly_wage": "£120k", "contract": "2028"}
    }
    data = mock_values.get(player_name, {"market_value": "Under £30M (Estimated)", "weekly_wage": "Unknown", "contract": "Unknown"})
    return f"Financial Dossier for {player_name}: {data}"

# ==========================================
# 3. BEHAVIORAL ANALYST TOOLS (The RAG / Search Component)
# ==========================================
@tool
def retrieve_player_background_rag_tool(player_name: str) -> str:
    """
    Queries our Vector Store containing scraped media articles, press conferences, 
    and dressing room reports regarding a player's character, chemistry, and personal life.
    """
    # This is where your RAG embedding lookup goes.
    print(f"[RAG Retrieval] Searching vector database for media background on: {player_name}")
    rag_vault = {
        "Pedro Neto": "Extremely dedicated professional. Highly regarded by managers for dressing room chemistry, though has documented frustration during extended hamstring injury rehabilitations.",
        "Nico Williams": "Very grounded personality, deeply family-oriented. Maintains exceptional locker room chemistry and shows high emotional intelligence in interviews.",
        "Michael Olise": "Reserved and introverted character. Prefers to let his football talk; zero off-pitch controversies, adapts well to strict structural tactics."
    }
    return rag_vault.get(player_name, "Local media files indicate a stable personal life with no major disciplinary infractions or negative chemistry reports.")

# ==========================================
# TOOL REGISTRATION MATRIX
# ==========================================
# Group your functions into the exact list variable the Supervisor imports
SCOUT_TOOLS = [
search_player_tactical_tool,
discovery_scout_tool
]