"""
Scout Engine Module
Acts as the orchestration layer. It merges independent cached datasets (Understat, FBref) 
and provides atomic data-access functions optimized for AI agents.
"""

from .scout_engine import ScoutEngine

# Exposes the ScoutEngine class to the rest of the workspace cleanly
__all__ = [
    "ScoutEngine"
]