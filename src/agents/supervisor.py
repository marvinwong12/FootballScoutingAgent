"""
AI Supervisor Module
Defines the LangGraph ReAct agent (The Chief Scout) that reasons through 
user queries and interacts with the data tools.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.agents.tools import SCOUT_TOOLS

# Load the API key from your hidden .env file
load_dotenv()

def build_chief_scout():
    """
    Initializes the LangGraph ReAct agent with explicit directives
    for handling per-90 metrics and custom tool sorting.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
    )

    # 💡 UPDATED PERSAONA: Explicitly guiding the LLM to use our new dynamic tool arguments
    system_prompt = (
        "You are the Chief Data Scout for a top-tier European football club. "
        "Your job is to discover and analyze talent using your unified analytics tools.\n\n"
        "CORE CAPABILITIES:\n"
        "1. When looking up an individual player, use search_player_tactical_tool. Remember that stats "
        "are normalized to lowercase, and look for both raw metrics and per-90 metrics (e.g., xg_per90).\n"
        "2. When searching the market for candidates, use discovery_scout_tool. You have full control "
        "to specify the position, max_value_millions, and filter or sort by per-90 metrics based on the request.\n\n"
        "CRITICAL RULES:\n"
        "- Never guess or make up data—always call the tools.\n"
        "- If a user asks for 'clinical finishers', filter or sort by 'xg_per90' or 'goals_per90'.\n"
        "- If a user asks for 'creative playmakers', filter or sort by 'key_passes_per90' or 'assists_per90'.\n"
        "- If a user asks for 'defensive steel', filter or sort by 'performance_tklw_per90' or 'performance_int_per90'.\n"
        "- Summarize all shortlists professionally with market valuations included."
    )

    app = create_react_agent(
        model=llm,
        tools=SCOUT_TOOLS,
        prompt=system_prompt
    )
    
    return app


# ==========================================
# LOCAL TESTING LOOP
# ==========================================
if __name__ == "__main__":
    print("Initializing LangGraph Chief Scout...")
    scout_app = build_chief_scout()
    print("Agent is online! Type 'quit' to exit.\n")
    
    while True:
        user_query = input("\nAsk the Chief Scout (e.g., 'What do you think of Bukayo Saka?'):\n> ")
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Shutting down scouting department...")
            break
            
        # 💡 ADD THIS LINE: Prevent empty submissions from hitting the LLM
        if not user_query.strip():
            continue
            
        print("\n--- CHIEF SCOUT EXECUTION TRACE ---")
        inputs = {"messages": [("user", user_query)]}
        
        # Stream updates as they happen node by node
        for chunk in scout_app.stream(inputs, stream_mode="updates"):
            for node, data in chunk.items():
                # Extract the last message from the active node
                if "messages" in data:
                    last_msg = data["messages"][-1]
                    
                    # If the model is choosing to call a tool:
                    if node == "agent" and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tool in last_msg.tool_calls:
                            print(f"🤖 [Reasoning] Chief Scout decided to use tool: {tool['name']}({tool['args']})")
                    
                    # If the tool is returning data back to the model:
                    elif node == "tools":
                        print(f"⚙️ [Data Layer] Tool executed successfully. Passing data back to LLM...")
                        
                    # If it's the final answer from the agent
                    elif node == "agent":
                        print("\n--- CHIEF SCOUT REPORT ---")
                        
                        # --- CLEANING THE RESPONSE ---
                        content = last_msg.content
                        
                        # If the output is a list containing a dict (like the SDK chunk), extract the text key
                        if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                            clean_text = content[0].get('text', str(content))
                            print(clean_text)
                        else:
                            print(content)
                            
                        print("--------------------------")