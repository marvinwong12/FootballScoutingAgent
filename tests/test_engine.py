# tests/test_engine.py
import os
import unittest
import pandas as pd
from src.engine import ScoutEngine

class TestScoutEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initializes the engine instance once before running the test cases."""
        current_file_path = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(current_file_path))
        
        # Point the engine to your scout cache directory
        cls.cache_dir = os.path.join(project_root, "data/scout_cache")
        cls.engine = ScoutEngine(cache_dir=cls.cache_dir)
        
        # Verify database initialization path integrity before proceeding
        if cls.engine._df is None or cls.engine._df.empty:
            raise unittest.SkipTest("Test skipped: Warm master dataset matrix cache is empty or missing.")

    def test_database_loading(self):
        """Ensure the master scouting matrix contains valid rows and identity keys."""
        df = self.engine._df
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0, "Master dataset should not be empty.")
        self.assertIn('player', df.columns, "Schema defect: 'player' key is missing.")
        self.assertIn('position', df.columns, "Schema defect: 'position' key is missing.")

    def test_player_lookup_success(self):
        """Verify atomic point-lookup returns a valid dictionary mapping for a known record."""
        # Grab a real player name present in your dataset to query
        sample_player = self.engine._df['player'].iloc[0]
        
        result = self.engine.lookup_player(sample_player)
        
        self.assertIsInstance(result, dict, f"Lookup should return a dict, got {type(result)} instead.")
        self.assertNotIn('match_name', result, "Security/Cleanliness: Internal key 'match_name' leaked in output.")
        self.assertFalse(any(isinstance(v, float) and v != v for v in result.values()), "JSON Trap: NaN float values leaked.")

    def test_player_lookup_failure(self):
        """Ensure point-lookup gracefully handles non-existent identities without throwing unhandled exceptions."""
        result = self.engine.lookup_player("NonExistent FakePlayer 99")
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("No scout target found matching:"))

    def test_positional_grouping_mapping(self):
        """Verify natural language string expansion maps correctly to dataset structural codes."""
        # Test if typing 'Defender' resolves and extracts only defensive elements
        filters = {"position": "Defender"}
        results = self.engine.discover_players(filters=filters, limit=10)
        
        self.assertIsInstance(results, list)
        for player in results:
            pos = player.get('position', '').lower()
            # Verify the record matches your underlying database alignment rules
            self.assertTrue(any(x in pos for x in ['df', 'd']), f"Positional leak: non-defender profile found: {pos}")

    def test_league_canonical_mapping(self):
        """Verify text normalization correctly translates long-form string variations."""
        filters = {"league": "Ligue 1"}
        results = self.engine.discover_players(filters=filters, limit=5)
        
        for player in results:
            # Enforce case-insensitivity on the test assertion side
            league_val = str(player.get('league', '')).lower()
            self.assertEqual(league_val, 'epl', "League text normalization failed to map string to 'epl'.")

    def test_dynamic_performance_bounds(self):
        """Verify mathematical comparison filtering evaluates value assertions correctly."""
        # Query for high production output metrics
        filters = {"min_goals": 0.3} 
        results = self.engine.discover_players(filters=filters, limit=5)
        
        for player in results:
            # The engine automatically normalizes base queries to 'goals_per90'
            goals_p90 = player.get('goals_per90', 0)
            self.assertGreaterEqual(goals_p90, 0.3, f"Filtering violation: returned a profile with {goals_p90} goals/90.")

    def test_clinical_sorting_sequence(self):
        """Ensure custom semantic values like 'clinical' map perfectly to computed arrays."""
        results = self.engine.discover_players(filters={}, sort_by="clinical", limit=3)
        
        self.assertTrue(len(results) >= 1)
        if len(results) >= 2:
            # Check if values descend monotonically
            first_eff = results[0].get('finishing_efficiency', -99)
            second_eff = results[1].get('finishing_efficiency', -99)
            self.assertGreaterEqual(first_eff, second_eff, "Sorting violation: Finishing efficiency did not descend.")

if __name__ == "__main__":
    unittest.main()