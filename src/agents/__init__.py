"""
Agents module initialization.
Exposes the core supervisor agent and associated scouting tools.
"""

from .supervisor import supervisor_agent  # Adjust if your supervisor function/variable has a different name
from .tools import (
    search_player_tactical_tool,
    discovery_scout_tool,
    query_player_narrative_tool,
    generate_percentile_comparison_chart,
    narrative_repo
)

__all__ = [
    "supervisor_agent",
    "discovery_scout_tool",
    "query_player_narrative_tool",
    "search_player_tactical_tool",
    "generate_percentile_comparison_chart",
    "narrative_repo"
]