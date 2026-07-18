import streamlit as st
from src.agents.supervisor import build_chief_scout
import json
import os
import re
from PIL import Image

# 1. Page Configuration
st.set_page_config(
    page_title="Chief Scout OS",
    page_icon="⚽",
    layout="centered"
)

st.title("⚽ Chief Scout OS")
st.markdown("Interact with your AI scouting department.")

# 2. Initialize the LangGraph Agent (Run once per session)
if "scout_agent" not in st.session_state:
    st.session_state.scout_agent = build_chief_scout()
    
# 3. Initialize Chat History in Streamlit Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "I am the Chief Scout. Who are we looking for today?"
    })

# 4. Render the existing chat history on the screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # First render any conversational text
        if message.get("content"):
            st.markdown(message["content"])
        
        # Then redraw the image frame using PIL!
        if "image" in message and message["image"]:
            try:
                img = Image.open(message["image"])
                st.image(img, use_container_width=True)
            except FileNotFoundError:
                st.error(f"Could not find the chart file at: {message['image']}")

# 5. Capture user input
user_query = st.chat_input("Ask your scouting agent a question...")

if user_query:
    # A. Display the user's message immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # B. Add user message to session state
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # C. Display a loading spinner while the agent thinks
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        inputs = {"messages": [("user", user_query)]}
        config = {"configurable": {"thread_id": "streamlit_session_1"}}
        
        with st.spinner("Scouting database and generating visualization..."):
            final_state = st.session_state.scout_agent.invoke(inputs, config=config)
            
            raw_content = final_state["messages"][-1].content
            
            if isinstance(raw_content, list):
                if len(raw_content) > 0 and isinstance(raw_content[0], dict) and "text" in raw_content[0]:
                    response_payload = raw_content[0]["text"]
                else:
                    response_payload = str(raw_content)
            else:
                response_payload = raw_content

            # --- THE NEW REGEX PARSING LOGIC ---
            image_path = None
            clean_text = response_payload

            # 1. Detect if the LLM wrapped the file in Markdown: ![Alt Text](filename.png)
            markdown_img_match = re.search(r"!\[.*?\]\((.*?\.png)\)", response_payload, re.IGNORECASE)
            
            if markdown_img_match:
                image_path = markdown_img_match.group(1)
                # Strip the broken markdown tag out of the text so we don't render a broken icon
                clean_text = re.sub(r"!\[.*?\]\(.*?\.png\)", "", response_payload, flags=re.IGNORECASE).strip()
            else:
                # 2. Fallback: Check if it returned raw JSON instead
                clean_payload = response_payload.strip()
                if clean_payload.startswith("```json"):
                    clean_payload = clean_payload.replace("```json", "").replace("```", "").strip()
                elif clean_payload.startswith("```"):
                    clean_payload = clean_payload.replace("```", "").strip()
                
                try:
                    parsed_json = json.loads(clean_payload)
                    if isinstance(parsed_json, dict) and "image_file" in parsed_json:
                        image_path = parsed_json["image_file"]
                        clean_text = "📊 *Generated percentile chart comparison for your request.*"
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

        # D. Display and save the response
        if image_path:
            absolute_image_path = os.path.abspath(image_path)
            
            try:
                # Force load the image data into memory using PIL
                img = Image.open(absolute_image_path)
                
                # Render any conversational text from the agent FIRST
                if clean_text:
                    message_placeholder.markdown(clean_text)
                else:
                    message_placeholder.empty()
                    
                # Render the pixel data natively BELOW the text
                st.image(img, use_container_width=True)
                
                # Save BOTH to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clean_text,
                    "image": absolute_image_path 
                })
            except FileNotFoundError:
                message_placeholder.error(f"Error: The chart was generated but Streamlit could not locate it at: {absolute_image_path}")
                
        else:
            # Fall back to standard markdown text for normal scouting answers
            message_placeholder.markdown(clean_text)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": clean_text
            })