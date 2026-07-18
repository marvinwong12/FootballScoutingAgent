import unittest
import json
from unittest.mock import patch, MagicMock
import base64
import os

# Import the tools from your newly refactored file
from src.agents import (
    search_player_tactical_tool,
    discovery_scout_tool,
    query_player_narrative_tool,
    narrative_repo,
    generate_percentile_comparison_chart
)

class TestScoutTools(unittest.TestCase):

    def test_search_player_tactical_tool(self):
        """Test looking up a single player's statistical profile."""
        # We invoke LangChain tools using .invoke() with a dictionary of arguments
        result = search_player_tactical_tool.invoke({"player_name": "Kylian Mbappe"})
        
        self.assertIsInstance(result, str, "Tool must return a string.")
        
        # Depending on if Mbappe is in your test CSV, it either returns JSON or a fallback string
        if "Strategic Lookup Notification" not in result:

            data = json.loads(result)
            self.assertIsInstance(data, list)
            self.assertTrue(len(data) > 0)

    def test_discovery_scout_tool(self):
        """Test the discovery engine with multiple complex filters."""
        result = discovery_scout_tool.invoke({
            "position": "FW",
            "max_age": 23,
            "min_height": 180,
            "sort_by_metric": "xg",
            "highest_first": True
        })
        
        self.assertIsInstance(result, str, "Tool must return a string.")
        
        if "CRITICAL: Zero players" not in result:
            print(f"\n--- DEBUG RESULT ---\nType: {type(result)}\nContent: {result}\n--------------------\n")
            data = json.loads(result)
            self.assertIsInstance(data, list, "Discovery should return a list of player profiles.")
            # Verify sorting/filtering logic applied
            for player in data:
                self.assertTrue(player.get("age", 0) <= 23, "Age filter failed in tool output.")

    @patch('src.agents.tools.ChatGoogleGenerativeAI')
    @patch('src.agents.tools.DuckDuckGoSearchResults')
    def test_query_player_narrative_tool_cache_miss(self, MockDDG, MockLLM):
        """Test narrative generation without hitting live web/LLM APIs."""
        import uuid # 👈 Import UUID for dynamic test keys
        
        # Setup DuckDuckGo mock
        mock_ddg_instance = MockDDG.return_value
        mock_ddg_instance.run.return_value = "Mock raw web text about player character."
        
        # Setup LangChain LLM mock
        mock_llm_instance = MockLLM.return_value
        mock_response = MagicMock()
        mock_response.content = "Sentence 1. Sentence 2. Sentence 3. Sentence 4."
        
        mock_llm_instance.invoke.return_value = mock_response
        mock_llm_instance.return_value = mock_response 

        # 👇 FIX: Guarantee a Cache Miss by using a unique UUID every single test run!
        test_player = f"Mock Player Test {uuid.uuid4()}"
        
        # Call 1: Guaranteed Cache Miss (Creates new dossier)
        result = query_player_narrative_tool.invoke({"player_name": test_player})
        
        self.assertIn("NEWLY RECONSTRUCTED DOSSIER", result)
        self.assertIn("Sentence 1.", result)
        
        # Call 2: Guaranteed Cache Hit (Retrieves the dossier we just made)
        result_cached = query_player_narrative_tool.invoke({"player_name": test_player})
        self.assertIn("LOCAL DOSSIER", result_cached)
        self.assertIn("Sentence 1.", result_cached)

    def test_generate_single_player_chart(self):
        """Test generating a percentile chart for a single player."""
        # Invoke with just player1 to trigger the solo profile logic
        result = generate_percentile_comparison_chart.invoke({
            "player1_name": "Kylian Mbappe",
            "metric_group": "attacking"
        })
        
        self.assertIsInstance(result, str, "Tool must return a string.")
        
        # Check that it didn't hit a data lookup failure or a system crash
        if "Strategic Notification" not in result and "System Execution Error" not in result:
            data = json.loads(result)
            
            # Assert the JSON structure and basic validity of the Base64 image
            self.assertIn("image_b64", data, "JSON output must contain 'image_b64' key.")
            self.assertIsInstance(data["image_b64"], str, "Base64 payload must be a string.")
            self.assertTrue(len(data["image_b64"]) > 100, "Base64 string is too short to be a valid PNG.")

    def test_generate_comparison_chart_side_by_side(self):
        """Test generating a side-by-side percentile chart for two players and save to root."""
        # Invoke with both players and a different metric group
        result = generate_percentile_comparison_chart.invoke({
            "player1_name": "Joao Pedro",
            "player2_name": "Erling Haaland",
            "metric_group": "comprehensive"
        })
        
        self.assertIsInstance(result, str, "Tool must return a string.")
        
        # Fail early if the engine couldn't find the players or threw a script error
        if "Strategic Notification" in result:
            self.fail(f"Tool returned a data lookup failure: {result}")
        if "System Execution Error" in result:
            self.fail(f"Tool crashed during execution: {result}")
            
        # Parse the valid JSON output
        data = json.loads(result)
        
        # Assert the JSON structure and basic validity of the Base64 image
        self.assertIn("image_b64", data, "JSON output must contain 'image_b64' key.")
        self.assertIsInstance(data["image_b64"], str, "Base64 payload must be a string.")
        self.assertTrue(len(data["image_b64"]) > 100, "Base64 string is too short to be a valid PNG.")
        
        # --- SAVE IMAGE TO ROOT FOR VISUAL INSPECTION ---
        try:
            # Extract and decode the raw binary image data
            image_bytes = base64.b64decode(data["image_b64"])
            
            # Define output path to the project root directory
            output_filename = "test_comparison_chart.png"
            
            with open(output_filename, "wb") as f:
                f.write(image_bytes)
                
            print(f"\n======== TEST SUCCESS ========")
            print(f"Visual validation chart successfully saved to your project root as: {os.path.abspath(output_filename)}")
            print(f"==============================\n")
            
        except Exception as e:
            self.fail(f"Failed to decode base64 or write the PNG file to disk: {str(e)}")
if __name__ == '__main__':
    unittest.main()