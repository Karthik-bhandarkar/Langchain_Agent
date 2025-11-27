import os
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient

# =========================
# ENV LOADING
# =========================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

# =========================
# MONGODB SETUP
# =========================

client = MongoClient(MONGO_URI)
db = client["agent_db"]

facts_collection = db["facts"]
conversation_collection = db["conversations"]

# =========================
# LANGCHAIN IMPORTS
# =========================

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# =========================
# FASTAPI APP
# =========================

app = FastAPI(title="AI Agent Backend with MongoDB + Smart Routing")

# =========================
# LLM SETUP
# =========================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY
)

# =========================
# EMOTION DETECTION
# =========================

def detect_emotional_state(text: str) -> bool:
    """
    AI-based detection of emotional distress.
    Returns True if emotional distress is detected.
    """

    prompt = f"""
    If this message expresses sadness, loneliness, stress, anxiety or depression,
    return ONLY "YES". Otherwise return ONLY "NO".

    Message: "{text}"
    """

    try:
        response = llm.invoke(prompt)
        result = response.content.strip().upper()
        return result == "YES"
    except:
        return False

# =========================
# SMART MARKS DETECTION
# =========================

def detect_marks_query(text: str) -> bool:
    """
    Detect if a message is asking about student marks without keywords.
    """
    names = ["priya", "amit", "rahul"]
    subjects = ["english", "maths", "science"]

    t = text.lower()

    return any(name in t for name in names) and any(sub in t for sub in subjects)

# =========================
# TOOLS
# =========================

@tool
def positive_prompt_tool(prompt: str) -> str:
    """
    Provides emotional encouragement and supportive response.
    """
    return f"Stay strong. Your message: '{prompt}'. You’re not alone, things will get better."

@tool
def negative_prompt_tool(prompt: str) -> str:
    """
    Generates a negative/exclusion style response.
    """
    return f"Negative version: {prompt} seems very difficult and unlikely."

@tool
def student_marks_tool(info: str) -> str:
    """
    Takes input like: Name,Subject
    Returns marks and grade for the student.
    """

    STUDENT_MARKS_DB = {
        "Priya": {"English": 92, "Maths": 88, "Science": 95},
        "Amit": {"English": 78, "Maths": 81, "Science": 74},
        "Rahul": {"English": 67, "Maths": 72, "Science": 70},
    }

    try:
        parts = info.replace("?", "").split()
        name = parts[0].capitalize()
        subject = parts[-1].capitalize()
    except:
        return "Invalid input format. Try: Priya Science"

    if name not in STUDENT_MARKS_DB:
        return f"No data found for {name}."

    if subject not in STUDENT_MARKS_DB[name]:
        return f"{name} has no marks stored for {subject}."

    marks = STUDENT_MARKS_DB[name][subject]

    grade = (
        "A+" if marks >= 90 else
        "A" if marks >= 80 else
        "B" if marks >= 70 else
        "C"
    )

    return f"{name} scored {marks} in {subject} (Grade: {grade})."

@tool
def suicide_related_tool(text: str) -> str:
    """
    Provides safe support for self-harm related messages.
    """
    return (
        "I'm really sorry you're feeling this way. "
        "Please reach out to someone you trust or a mental health professional. "
        "You are not alone, and support is available."
    )

tools = [
    positive_prompt_tool,
    negative_prompt_tool,
    student_marks_tool,
    suicide_related_tool
]

# =========================
# ROUTER LOGIC
# =========================

def get_route(text: str) -> str:

    t = text.lower()

    crisis_keywords = ["suicide", "kill myself", "want to die", "end my life", "worthless"]
    if any(word in t for word in crisis_keywords):
        return "suicide_related_tool"

    if "negative prompt" in t or "avoid" in t or "exclude" in t:
        return "negative_prompt_tool"

    if detect_marks_query(text):
        return "student_marks_tool"

    if detect_emotional_state(text):
        return "positive_prompt_tool"

    return "no_tool"

# =========================
# MEMORY
# =========================

session_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# =========================
# MONGODB HELPERS
# =========================

def save_conversation(session_id, user_msg, ai_msg, tool_used):
    conversation_collection.insert_one({
        "session_id": session_id,
        "user": user_msg,
        "assistant": ai_msg,
        "tool_used": tool_used,
        "timestamp": datetime.utcnow()
    })

def get_history(session_id):
    history = conversation_collection.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1)

    return list(history)

# =========================
# AGENT SETUP
# =========================

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use tools when necessary."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

main_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=session_memory,
    verbose=False
)

# =========================
# MAIN PIPELINE
# =========================

def run_pipeline(user_input: str, session_id: str) -> str:

    tool_used = get_route(user_input)

    # Force tool triggering
    if tool_used != "no_tool":
        response = tools[[t.name for t in tools].index(tool_used)](user_input)
    else:
        result = main_agent.invoke({"input": user_input})
        response = result["output"]

    save_conversation(session_id, user_input, response, tool_used)
    return response

# =========================
# API MODELS
# =========================

class ChatRequest(BaseModel):
    session_id: str
    message: str

# =========================
# ROUTES
# =========================

@app.post("/chat")
async def chat(req: ChatRequest):
    response = run_pipeline(req.message, req.session_id)

    return {
        "session_id": req.session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user": req.message,
        "response": response,
        "route_selected": get_route(req.message)
    }

@app.get("/history/{session_id}")
async def fetch_history(session_id: str):
    history = get_history(session_id)
    return {"session_id": session_id, "history": history}

@app.delete("/reset-history/{session_id}")
async def reset_history(session_id: str):
    conversation_collection.delete_many({"session_id": session_id})
    return {"status": f"Session {session_id} history reset successfully"}

@app.get("/")
def home():
    return {"status": "AI Agent Backend Running ✅"}
