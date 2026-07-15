"""
Smashing Monkeys - Football Scouting Platform Core API Gateway
Exposes primary execution engines, ingestion pipelines, helper utilities, and tool namespaces cleanly to the application workspace.
"""

import logging

# 1. Package Metadata Definitions
__version__ = "1.0.0"
__author__ = "Marvin Wong"

# 2. Package-Level Telemetry Initialization
# Ensures that any tool or module running inside src/ has a unified logging context
logging.getLogger("scout_platform").addHandler(logging.NullHandler())

# 3. Gateway Imports
try:
    # A. Core Processing Engine
    from src.engine.scout_engine import ScoutEngine
    
    # B. ETL / Ingestion Pipeline & Proprietary Narrative Management
    from src.ingestion.compile_master import compile_master_dataset
    from src.ingestion.ingest_narratives import (
        add_custom_scouting_report,
        get_vector_collection
    )
    
    # C. Intelligent Agents & Scouting Tools
    from src.agents import (
        search_player_tactical_tool,
        discovery_scout_tool,
        query_player_narrative_tool,
        generate_percentile_comparison_chart,
        narrative_repo
    )

    # D. Common Helper Utilities
    from src.helper_functions import normalize_name

except ImportError as e:
    # Diagnostic fallback to prevent silent workspace path resolution crashes
    raise ImportError(
        f"Critical Failure exposing core platform layers via API Gateway: {e}\n"
        "Ensure your PYTHONPATH environment tracking variable includes the project root."
    )

# 4. Define Strict Export Boundary Matrix
# This tells Python exactly what classes/functions are public when someone runs: from src import *
__all__ = [
    "ScoutEngine",
    "compile_master_dataset",
    "add_custom_scouting_report",
    "get_vector_collection",
    "search_player_tactical_tool",
    "discovery_scout_tool",
    "query_player_narrative_tool",
    "generate_percentile_comparison_chart",
    "narrative_repo",
    "normalize_name",
]