import streamlit as st
import requests
import uuid
from datetime import datetime

# ==========================
# CONFIG
# ==========================

API_URL = "http://127.0.0.1:8000/chat"
HISTORY_URL = "http://127.0.0.1:8000/history"
RESET_URL = "http://127.0.0.1:8000/reset-history"

st.set_page_config(
    page_title="AI Agent Chat",
    layout="centered"
)

st.title("🤖 AI Agent Chat")
st.caption("FastAPI + MongoDB + Tool Detection Enabled")

# ==========================
# SESSION SETUP
# ==========================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "loaded" not in st.session_state:
    st.session_state.loaded = False

# ==========================
# SIDEBAR
# ==========================

st.sidebar.header("Session Control")

st.sidebar.markdown("### Current Session ID")
st.sidebar.code(st.session_state.session_id)

if st.sidebar.button("New Session"):
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state.chat_history = []
    st.session_state.loaded = False
    st.rerun()

if st.sidebar.button("Reset Mongo History"):
    try:
        requests.delete(f"{RESET_URL}/{st.session_state.session_id}")
        st.session_state.chat_history = []
        st.session_state.loaded = False
        st.success("✅ Session history cleared from MongoDB")
        st.rerun()
    except:
        st.error("❌ Failed to reset Mongo history")

# ==========================
# LOAD BACKEND HISTORY
# ==========================

if not st.session_state.loaded:
    try:
        r = requests.get(f"{HISTORY_URL}/{st.session_state.session_id}").json()

        for item in r["history"]:
            timestamp = item.get("timestamp", "")
            tool = item.get("tool_used", "no_tool")

            time_str = timestamp.split("T")[1][:8] if timestamp else ""

            st.session_state.chat_history.append(
                ("user", f"🕒 {time_str} — {item['user']}")
            )

            st.session_state.chat_history.append(
                ("assistant", f"🛠 Tool: `{tool}`\n\n🕒 {time_str} — {item['assistant']}")
            )

        st.session_state.loaded = True

    except Exception as e:
        st.warning("⚠ Could not load history from backend")

# ==========================
# DISPLAY HISTORY
# ==========================

for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# ==========================
# CHAT INPUT
# ==========================

user_input = st.chat_input("Type your message...")

if user_input:

    timestamp = datetime.now().strftime("%H:%M:%S")

    st.session_state.chat_history.append(
        ("user", f"🕒 {timestamp} — {user_input}")
    )

    with st.chat_message("user"):
        st.markdown(f"🕒 {timestamp} — {user_input}")

    try:
        r = requests.post(
            API_URL,
            json={
                "session_id": st.session_state.session_id,
                "message": user_input
            }
        ).json()

        reply = r.get("response", "")
        tool_used = r.get("route_selected", "no_tool")

    except Exception as e:
        reply = f"❌ Backend error: {e}"
        tool_used = "error"

    st.session_state.chat_history.append(
        ("assistant", f"🛠 Tool: `{tool_used}`\n\n🕒 {timestamp} — {reply}")
    )

    with st.chat_message("assistant"):
        st.markdown(f"🛠 Tool: `{tool_used}`\n\n🕒 {timestamp} — {reply}")
