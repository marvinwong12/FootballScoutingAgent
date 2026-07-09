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
    # Add max_retries to handle the Free Tier pacing effortlessly
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        max_retries=6,  # Will automatically retry with exponential backoff
        temperature=0.2
)

    # UPDATED PERSAONA: Explicitly guiding the LLM to use our new dynamic tool arguments
    system_prompt = (
        "You are the Chief Data Scout for a top-tier European football club. "
        "Your job is to discover and analyze talent using your unified analytics tools.\n\n"
        "FOOTBALL INTELLIGENCE & SEMANTIC MAPPING:\n"
        "Do not look for literal words. Use your advanced knowledge of football tactics and analytics "
        "to translate abstract user phrases into our specific database schema. For example, map concepts like "
        "'ball-progression' to xg_chain, 'ball-winner' to tackles/interceptions, or 'creative hub' to key passes.\n\n"
        "YOUR AVAILABLE PERFORMANCE SCHEMA:\n"
        "When filtering or sorting, you MUST map your tactical intent to these exact column strings:\n"
        "• Attacking Output: 'goals_per90', 'xg_per90', 'shots_per90'\n"
        "• Playmaking & Progression: 'assists_per90', 'xa_per90', 'key_passes_per90', 'xg_chain_per90', 'xg_buildup_per90'\n"
        "• Defensive Steel & Discipline: 'performance_tklw_per90', 'performance_int_per90', 'ball_recoveries_per90', 'performance_fls_per90', 'performance_crdy_per90'\n"
        "• Financial Constraints: 'market_value_mln', 'contract_expiry'\n\n"
        "CRITICAL RULES:\n"
        "1. Never invent or hallucinate metrics. You must map user requests strictly to the exact database schema names listed above.\n"
        "2. Always utilize the search or discovery tools to back up your assessments; do not guess stats.\n"
        "3. Provide deep tactical reasoning in your reports explaining why your discovered players match the user's scouting brief."
    )

    # MemorySaver keeps the context buffer inside active RAM memory for the thread session
    checkpointer = MemorySaver()

    # Build the LangGraph Application with memory checkpointer compiled natively
    app = create_react_agent(
        model=llm,
        tools=SCOUT_TOOLS,
        prompt=system_prompt,
        checkpointer=checkpointer  # REGISTER CHECKPOINTER
    )
    
    return app


# ==========================================
# LOCAL TESTING LOOP
# ==========================================
if __name__ == "__main__":
    print("Initializing Stateful LangGraph Chief Scout...")
    
    # Build the ReAct state machine graph compiled with MemorySaver
    scout_app = build_chief_scout()
    print("Agent is online! Memory system activated. Type 'quit' to exit.\n")
    
    # STATEFUL SESSION ID CONFIGURATION:
    # LangGraph's MemorySaver checkpointer relies on a unique 'thread_id' key.
    # As long as this exact thread_id string is passed into future calls, the 
    # engine will automatically append new chat turns onto the existing conversation history.
    session_config = {"configurable": {"thread_id": "scout_terminal_session_alpha"}}
    
    # Main interactive loop to chat with the agent via the terminal
    while True:
        user_query = input("\nAsk the Chief Scout:\n> ")
        
        # Guardrail: Cleanly break the loop if the user wants to close the program
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Shutting down scouting department...")
            break
            
        # Guardrail: Skip empty entries or accidental "Enter" keystrokes to prevent empty API payloads
        if not user_query.strip():
            continue
            
        print("\n--- CHIEF SCOUT EXECUTION TRACE ---")
        
        # Wrap the user's string in LangChain's expected message payload format
        inputs = {"messages": [("user", user_query)]}
        
        # GRAPH STREAMING INTERACTION:
        # We invoke .stream() to watch the agent reason through nodes step-by-step.
        # We explicitly supply 'config=session_config' so the graph loads the message history 
        # from MemorySaver BEFORE running, and commits the final response back to that thread when finished.
        for chunk in scout_app.stream(inputs, config=session_config, stream_mode="updates"):
            
            # A 'chunk' represents a state transition update from an individual graph node
            for node, data in chunk.items():
                
                # Check if the currently executing node generated a new message
                if "messages" in data:
                    # Isolate the very latest message object appended to the state channel
                    last_msg = data["messages"][-1]
                    
                    # NODE DETECTOR A: The LLM is thinking/deciding
                    # If the 'agent' node is running and its message includes a 'tool_calls' payload,
                    # it means the model has determined it needs to look up data from our CSV tables.
                    if node == "agent" and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tool in last_msg.tool_calls:
                            print(f"🤖 [Reasoning] Chief Scout using tool: {tool['name']}({tool['args']})")
                    
                    # NODE DETECTOR B: The Tool execution box
                    # This tells you that the graph has successfully jumped over to the execution layer,
                    # read the target CSV sheets via pandas, and is returning the dictionary rows to the LLM.
                    elif node == "tools":
                        print(f"⚙️ [Data Layer] Processing completed successfully. Returning state to LLM...")
                        
                    # NODE DETECTOR C: The Final Response
                    # If the 'agent' node is running but does NOT want to call a tool, it means the model
                    # has all the facts it needs and is generating its final scout report back to the user.
                    elif node == "agent":
                        print("\n--- CHIEF SCOUT REPORT ---")
                        content = last_msg.content
                        
                        # Data-cleaning fallback: Some versions of the LangChain Google SDK pack text
                        # into an inner list of dictionaries rather than a clean raw string.
                        if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
                            clean_text = content[0].get('text', str(content))
                            print(clean_text)
                        else:
                            # Standard string printing
                            print(content)
                        print("--------------------------")