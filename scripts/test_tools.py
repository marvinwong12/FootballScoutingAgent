import unittest
import json
import os
import base64
from unittest.mock import patch, MagicMock

# Import the tools from your workspace package layer
from src.agents.tools import (
    search_player_tactical_tool,
    discovery_scout_tool,
    query_player_narrative_tool,
    generate_percentile_comparison_chart
)

class TestScoutTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create an output directory for visual validation checks."""
        cls.output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(cls.output_dir, exist_ok=True)

    def test_search_player_tactical_tool(self):
        """Test looking up a single player's statistical profile."""
        result = search_player_tactical_tool.invoke({"player_name": "Kylian Mbappe"})
        self.assertIsInstance(result, str)
        if "Strategic Lookup Notification" not in result:
            data = json.loads(result)
            self.assertIsInstance(data, list)

    def test_discovery_scout_tool(self):
        """Test the discovery engine with multiple complex filters."""
        result = discovery_scout_tool.invoke({
            "position": "FW",
            "max_age": 23,
            "sort_by_metric": "xg",
            "highest_first": True
        })
        self.assertIsInstance(result, str)
        if "CRITICAL: Zero players" not in result:
            data = json.loads(result)
            self.assertIsInstance(data, list)

    def test_generate_percentile_comparison_chart_solo(self):
        """Test generating a solo profile chart and outputting it for verification."""
        # Grab a player you know exists in your master cache
        result = generate_percentile_comparison_chart.invoke({
            "player1_name": "Kylian Mbappe",
            "metric_group": "attacking"
        })
        
        self.assertIsInstance(result, str)
        
        # If the player exists and was plotted successfully
        if "Strategic Notification" not in result:
            payload = json.loads(result)
            self.assertIn("image_b64", payload)
            
            # Decode and write the image out to disk so you can visually inspect it
            image_data = base64.b64decode(payload["image_b64"])
            output_path = os.path.join(self.output_dir, "test_mbappe_solo.png")
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            self.assertTrue(os.path.exists(output_path), "Failed to write visual asset to disk.")

    def test_generate_percentile_comparison_chart_duo(self):
        """Test generating a dual side-by-side player comparison chart."""
        result = generate_percentile_comparison_chart.invoke({
            "player1_name": "Jude Bellingham",
            "player2_name": "Gavi",
            "metric_group": "comprehensive"
        })
        
        self.assertIsInstance(result, str)
        
        if "Strategic Notification" not in result:
            payload = json.loads(result)
            self.assertIn("image_b64", payload)
            
            # Decode and save the dual comparison chart
            image_data = base64.b64decode(payload["image_b64"])
            output_path = os.path.join(self.output_dir, "test_bellingham_vs_gavi.png")
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            self.assertTrue(os.path.exists(output_path))

    @patch('src.agents.tools.ChatGoogleGenerativeAI')
    @patch('src.agents.tools.DuckDuckGoSearchResults')
    def test_query_player_narrative_tool_cache_miss(self, MockDDG, MockLLM):
        """Test narrative generation without hitting live web/LLM APIs."""
        import uuid # Ensure random generation is available
        
        mock_ddg_instance = MockDDG.return_value
        mock_ddg_instance.run.return_value = "Mock raw web text about player character."
        
        mock_llm_instance = MockLLM.return_value
        mock_response = MagicMock()
        mock_response.content = "Sentence 1. Sentence 2. Sentence 3. Sentence 4."
        
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_instance.return_value = mock_response 

        # 👇 FIX: Generate a completely unique player name every time the test runs
        test_player = f"Mock Player {uuid.uuid4()}"
        
        # 1. Force a Cache Miss (Guaranteed because the name is randomly generated)
        result = query_player_narrative_tool.invoke({"player_name": test_player})
        self.assertIn("NEWLY RECONSTRUCTED DOSSIER", result)
        self.assertIn("Sentence 1.", result)
        
        # 2. Test the Cache HIT works immediately after for that exact same unique name
        result_cached = query_player_narrative_tool.invoke({"player_name": test_player})
        self.assertIn("LOCAL DOSSIER", result_cached)
        self.assertIn("Sentence 1.", result_cached)

if __name__ == '__main__':
    unittest.main()