"""
AI Supervisor Module
Defines the LangGraph ReAct agent (The Chief Scout) that reasons through 
user queries and interacts with the data tools.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from src.agents.tools import SCOUT_TOOLS

# Load the API key from your hidden .env file
load_dotenv()

def build_chief_scout():
    """
    Initializes the LangGraph ReAct agent with explicit directives
    for handling per-90 metrics, wages, ages, and custom tool sorting.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        max_retries=6, 
        temperature=0.7
    )

    # 💡 THE UPDATE: Added explicit instructions on when and how to use the RAG tool
    system_prompt = (
        "You are the Chief Data Scout for a top-tier European football club. "
        "Your job is to discover and analyze talent using your unified analytics tools.\n\n"
        "FOOTBALL INTELLIGENCE & SEMANTIC MAPPING:\n"
        "Do not look for literal words. Use your advanced knowledge of football tactics and analytics "
        "to translate abstract user phrases into our specific database schema.\n"
        "• Map concepts like 'ball-progression' to xg_chain, 'ball-winner' to tackles/interceptions.\n"
        "• Map concepts like 'youngster', 'wonderkid', or 'prospect' to age thresholds.\n"
        "• Map concepts like 'cheap salary' or 'low earner' to annual_wage_eur.\n\n"
        "YOUR AVAILABLE SCHEMA MATRIX:\n"
        "When filtering or sorting, you MUST map your tactical/financial intent to these exact column strings:\n"
        "• Attacking Output: 'goals_per90', 'xg_per90', 'shots_per90'\n"
        "• Playmaking & Progression: 'assists_per90', 'xa_per90', 'key_passes_per90', 'xg_chain_per90', 'xg_buildup_per90'\n"
        "• Defensive Steel & Discipline: 'performance_tklw_per90', 'performance_int_per90', 'ball_recoveries_per90', 'performance_fls_per90', 'performance_crdy_per90'\n"
        "• Financial Constraints: 'market_value_mln', 'contract_expiry', 'annual_wage_eur', 'age', 'nation'\n\n"
        "QUALITATIVE & RISK VETTING (NEW DIRECTIVE):\n"
        "After finding a shortlist of players using your structured data tools, you MUST use the "
        "'query_player_narrative_tool' to check their qualitative profiles. \n"
        "• If the user asks about injuries, character, or tactical fit, query the narrative tool for the specific player.\n"
        "• Synthesize both the raw numbers and the text reports into your final scouting brief.\n\n"
        "CRITICAL RULES:\n"
        "1. Never invent or hallucinate metrics, injury histories, or character traits. Rely STRICTLY on your tools.\n"
        "2. When the user sets a maximum age, wage, or transfer value constraint, you MUST explicitly pass those numeric values into the corresponding arguments of the discovery tool: 'max_age', 'max_wage', and 'max_value_millions'.\n"
        "3. Do not run generic searches dropping filters unless explicitly asked to broaden the range by the user."
    )

    checkpointer = MemorySaver()

    app = create_react_agent(
        model=llm,
        tools=SCOUT_TOOLS,
        prompt=system_prompt,
        checkpointer=checkpointer 
    )
    
    return app


# ==========================================
# LOCAL TESTING LOOP
# ==========================================
if __name__ == "__main__":
    print("Initializing Stateful LangGraph Chief Scout...")
    
    scout_app = build_chief_scout()
    print("Agent is online! Memory system activated. Type 'quit' to exit.\n")
    
    session_config = {"configurable": {"thread_id": "scout_terminal_session_alpha"}}
    
    while True:
        user_query = input("\nAsk the Chief Scout:\n> ")
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Shutting down scouting department...")
            break
            
        if not user_query.strip():
            continue
            
        print("\n--- CHIEF SCOUT EXECUTION TRACE ---")
        
        inputs = {"messages": [("user", user_query)]}
        
        for chunk in scout_app.stream(inputs, config=session_config, stream_mode="updates"):
            for node, data in chunk.items():
                if "messages" in data:
                    last_msg = data["messages"][-1]
                    
                    if node == "agent" and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tool in last_msg.tool_calls:
                            print(f"🤖 [Reasoning] Chief Scout using tool: {tool['name']}({tool['args']})")
                    
                    elif node == "tools":
                        print(f"⚙️ [Data Layer] Processing completed successfully. Returning state to LLM...")
                        
                    elif node == "agent":
                        print("\n--- CHIEF SCOUT REPORT ---")
                        content = last_msg.content
                        
                        if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                            clean_text = content[0].get('text', str(content))
                            print(clean_text)
                        else:
                            print(content)
                        print("--------------------------")