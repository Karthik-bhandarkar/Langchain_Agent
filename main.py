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

app = FastAPI(title="AI Agent Backend (Auto Tool Selection)")

# =========================
# LLM SETUP
# =========================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
)

# =========================
# TOOLS (LLM WILL CHOOSE)
# =========================

@tool
def positive_prompt_tool(prompt: str) -> str:
    """
    Use this tool when the user or their friend seems emotionally low, lonely,
    stressed, sad, or in need of encouragement or motivation.
    It should return a warm, supportive, and uplifting response.
    """
    return (
        f"I hear that: '{prompt}'. "
        "It's completely okay to feel this way sometimes. "
        "You matter, and things can get better step by step. "
        "Try reaching out to someone you trust, and be kind to yourself."
    )


@tool
def negative_prompt_tool(prompt: str) -> str:
    """
    Use this tool when the user explicitly asks for a negative prompt,
    or to avoid/exclude something in an image or text generation prompt.
    Return a negative-style or exclusion-style rewrite of the prompt.
    """
    return f"Negative/exclusion-style version of your idea: Avoid {prompt}."


@tool
def student_marks_tool(query: str) -> str:
    """
    Use this tool when the user is asking about a student's marks, score,
    result, or grade in a specific subject.
    It expects a free-form query mentioning the student's name and subject.
    """

    STUDENT_MARKS_DB = {
        "Priya": {"English": 92, "Maths": 88, "Science": 95},
        "Amit": {"English": 78, "Maths": 81, "Science": 74},
        "Rahul": {"English": 67, "Maths": 72, "Science": 70},
    }

    q = query.replace("?", "").lower()

    name = None
    subject = None

    # rough auto-detection from text
    for n in STUDENT_MARKS_DB.keys():
        if n.lower() in q:
            name = n
            break

    for s in ["english", "maths", "science"]:
        if s in q:
            subject = s.capitalize()
            break

    if not name or not subject:
        return (
            "I couldn't clearly detect the name and subject. "
            "Please include both, like: 'What are Priya's Science marks?'."
        )

    if subject not in STUDENT_MARKS_DB[name]:
        return f"{name} has no marks stored for {subject}."

    marks = STUDENT_MARKS_DB[name][subject]

    if marks >= 90:
        grade = "A+"
    elif marks >= 80:
        grade = "A"
    elif marks >= 70:
        grade = "B"
    else:
        grade = "C"

    return f"{name} scored {marks} in {subject} (Grade: {grade})."


@tool
def suicide_related_tool(text: str) -> str:
    """
    ALWAYS use this tool when the user expresses suicidal thoughts,
    self-harm intent, or wants to end their life.
    It must respond with a very safe, supportive message and
    encourage contacting trusted people or professionals.
    """
    return (
        "I'm really sorry you're feeling this way. "
        "Your life is important and you deserve support. "
        "Please reach out immediately to someone you trust, a family member, "
        "friend, or local mental health professional. "
        "If you are in immediate danger, contact your local emergency services. "
        "You are not alone."
    )


tools = [
    positive_prompt_tool,
    negative_prompt_tool,
    student_marks_tool,
    suicide_related_tool,
]

# =========================
# MEMORY
# =========================

session_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
)

# =========================
# AGENT SETUP
# =========================

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a helpful AI assistant.\n\n"
                "- You have access to several tools.\n"
                "- Let the model automatically decide when to call them.\n"
                "- Use student_marks_tool for any question about student marks/grades.\n"
                "- Use positive_prompt_tool when the user or a friend seems emotionally low.\n"
                "- Use negative_prompt_tool when the user explicitly asks for a negative prompt or to avoid/exclude something.\n"
                "- For any mention of suicidal intent or self-harm, you MUST call suicide_related_tool.\n"
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

agent = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

# IMPORTANT: return_intermediate_steps=True to see which tools were used
main_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=session_memory,
    verbose=False,
    return_intermediate_steps=True,
)

# =========================
# DB HELPERS
# =========================

def save_conversation(session_id: str, user_msg: str, ai_msg: str, tool_used: str):
    conversation_collection.insert_one(
        {
            "session_id": session_id,
            "user": user_msg,
            "assistant": ai_msg,
            "tool_used": tool_used,
            "timestamp": datetime.utcnow(),
        }
    )


def get_history(session_id: str):
    history = (
        conversation_collection.find({"session_id": session_id}, {"_id": 0})
        .sort("timestamp", 1)
    )
    return list(history)


# =========================
# MAIN PIPELINE
# =========================

def run_pipeline(user_input: str, session_id: str):
    """
    Sends the user input to the LangChain agent.
    The agent automatically decides whether to use tools or not.
    We inspect intermediate_steps to see which tools were used.
    """

    try:
        result = main_agent.invoke({"input": user_input})

        # final model output
        response = result.get("output", "")

        # detect tool used from intermediate steps (if any)
        intermediate_steps = result.get("intermediate_steps", [])
        if intermediate_steps:
            # each step is (AgentAction, tool_output)
            last_action = intermediate_steps[-1][0]
            tool_used = getattr(last_action, "tool", "unknown_tool")
        else:
            tool_used = "no_tool"

    except Exception as e:
        response = f"Agent Error: {str(e)}"
        tool_used = "error"

    save_conversation(session_id, user_input, response, tool_used)

    return response, tool_used


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
    response, tool_used = run_pipeline(req.message, req.session_id)

    return {
        "session_id": req.session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user": req.message,
        "response": response,
        "route_selected": tool_used,  # this is what Streamlit shows as Tool
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
    return {"status": "AI Agent Backend (Auto Tool Selection) Running ✅"}
