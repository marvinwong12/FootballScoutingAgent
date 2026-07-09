"""
Data Ingestion Module
Handles all direct scraping and data collection from external sources (Understat, FBref).
"""

from .fetch_attacking import ingest_unified_attacking_data
from .fetch_defensive import ingest_unified_defensive_data

# The __all__ list explicitly defines what functions are exported when another file 
# runs: `from src.ingestion import *`. It keeps your namespace clean and secure.
__all__ = [
    "ingest_unified_attacking_data",
    "ingest_unified_defensive_data"
]