import streamlit as st
import requests
import uuid
from datetime import datetime

# Base URLs for communicating with FastAPI backend endpoints
API_URL = "http://127.0.0.1:8000/chat"
HISTORY_URL = "http://127.0.0.1:8000/history"
RESET_URL = "http://127.0.0.1:8000/reset-history"

# Configure Streamlit page settings
st.set_page_config(
    page_title="AI Agent Chat",
    layout="centered"
)

# Title and subtitle for the UI
st.title("🤖 AI Agent Chat")
st.caption("FastAPI + MongoDB + Tool Detection Enabled")

# Session ID initialization for tracking conversation state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

# Local chat history to display messages persistently on the UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Tracks if backend conversation history has already been loaded
if "loaded" not in st.session_state:
    st.session_state.loaded = False

# Sidebar controls for resetting session and clearing MongoDB history
st.sidebar.header("Session Control")

# Display session ID inside sidebar
st.sidebar.markdown("### Current Session ID")
st.sidebar.code(st.session_state.session_id)

# Button to start a fresh session (new session ID + clear local history)
if st.sidebar.button("New Session"):
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.chat_history = []
    st.session_state.loaded = False
    st.rerun()

# Button to clear backend MongoDB-stored conversation history
if st.sidebar.button("Reset Mongo History"):
    try:
        requests.delete(f"{RESET_URL}/{st.session_state.session_id}")
        st.session_state.chat_history = []
        st.session_state.loaded = False
        st.success("✅ Session history cleared from MongoDB")
        st.rerun()
    except:
        st.error("❌ Failed to reset Mongo history")

# Load previous messages from backend (only once per session load)
if not st.session_state.loaded:
    try:
        r = requests.get(f"{HISTORY_URL}/{st.session_state.session_id}").json()

        # Loop through stored history and convert to display format
        for item in r["history"]:
            timestamp = item.get("timestamp", "")
            tool = item.get("tool_used", "no_tool")

            # Extract only time from ISO timestamp
            time_str = timestamp.split("T")[1][:8] if timestamp else ""

            # Append user message to internal state
            st.session_state.chat_history.append(
                ("user", f"🕒 {time_str} — {item['user']}")
            )

            # Append assistant message along with detected tool
            st.session_state.chat_history.append(
                ("assistant", f"🛠 Tool: `{tool}`\n\n🕒 {time_str} — {item['assistant']}")
            )

        st.session_state.loaded = True

    except Exception as e:
        st.warning("⚠ Could not load history from backend")

# Display all messages in Streamlit chat container
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# Chat input field for user messages
user_input = st.chat_input("Type your message...")

if user_input:

    # Generate current timestamp for display
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Add user message to UI and internal history
    st.session_state.chat_history.append(
        ("user", f"🕒 {timestamp} — {user_input}")
    )

    with st.chat_message("user"):
        st.markdown(f"🕒 {timestamp} — {user_input}")

    try:
        # Send request to FastAPI backend for response
        r = requests.post(
            API_URL,
            json={
                "session_id": st.session_state.session_id,
                "message": user_input
            }
        ).json()

        # Extract assistant reply and tool used
        reply = r.get("response", "")
        tool_used = r.get("route_selected", "no_tool")

    except Exception as e:
        # Handle failure to contact backend
        reply = f"❌ Backend error: {e}"
        tool_used = "error"

    # Store assistant reply in history
    st.session_state.chat_history.append(
        ("assistant", f"🛠 Tool: `{tool_used}`\n\n🕒 {timestamp} — {reply}")
    )

    # Display assistant message in chat UI
    with st.chat_message("assistant"):
        st.markdown(f"🛠 Tool: `{tool_used}`\n\n🕒 {timestamp} — {reply}")
