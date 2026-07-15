"""
Ingestion module initialization.
Exposes data compilation pipelines and proprietary vector-database entrypoints.
"""

from .compile_master import compile_master_dataset
from .ingest_narratives import (
    add_custom_scouting_report,
    get_vector_collection
)

__all__ = [
    "compile_master_dataset",
    "add_custom_scouting_report",
    "get_vector_collection",
]