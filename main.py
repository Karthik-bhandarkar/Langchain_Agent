import os
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys and DB URI from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Ensure required environment variables exist
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

if not MONGO_URI:
    raise ValueError("MONGO_URI not found in .env")

# Connect to MongoDB using provided URI
client = MongoClient(MONGO_URI)
db = client["agent_db"]

# Collection to store chat conversations
conversation_collection = db["conversations"]

# LangChain imports used for LLM, tools, memory, agent, prompts
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# FastAPI application initialization
app = FastAPI(title="AI Agent Backend (Auto Tool Selection)")

# Create the ChatOpenAI model instance with deterministic behavior
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
)

# Tool: Generates positive, supportive messages for emotionally low users
@tool
def positive_prompt_tool(prompt: str) -> str:
    """
    Tool to generate warm and uplifting responses when emotional support is needed.
    """
    return (
        f"I hear that: '{prompt}'. "
        "It's completely okay to feel this way sometimes. "
        "You matter, and things can get better step by step. "
        "Try reaching out to someone you trust, and be kind to yourself."
    )

# Tool: Creates negative/exclusion-style prompts when explicitly requested
@tool
def negative_prompt_tool(prompt: str) -> str:
    """
    Tool to rewrite the user's prompt in a negative or exclusion-style format.
    """
    return f"Negative/exclusion-style version of your idea: Avoid {prompt}."

# Tool: Provides student marks based on a simple in-memory DB lookup
@tool
def student_marks_tool(query: str) -> str:
    """
    Tool that fetches marks/grades for a student and subject from a mock database.
    """
    STUDENT_MARKS_DB = {
        "Priya": {"English": 92, "Maths": 88, "Science": 95},
        "Amit": {"English": 78, "Maths": 81, "Science": 74},
        "Rahul": {"English": 67, "Maths": 72, "Science": 70},
    }

    q = query.replace("?", "").lower()

    name = None
    subject = None

    # Detect student name from text
    for n in STUDENT_MARKS_DB.keys():
        if n.lower() in q:
            name = n
            break

    # Detect subject from text
    for s in ["english", "maths", "science"]:
        if s in q:
            subject = s.capitalize()
            break

    # Return guidance if name/subject not detected
    if not name or not subject:
        return (
            "I couldn't clearly detect the name and subject. "
            "Please include both, like: 'What are Priya's Science marks?'."
        )

    # Ensure subject exists in student record
    if subject not in STUDENT_MARKS_DB[name]:
        return f"{name} has no marks stored for {subject}."

    marks = STUDENT_MARKS_DB[name][subject]

    # Simple grade calculation
    if marks >= 90:
        grade = "A+"
    elif marks >= 80:
        grade = "A"
    elif marks >= 70:
        grade = "B"
    else:
        grade = "C"

    return f"{name} scored {marks} in {subject} (Grade: {grade})."

# Tool: Mandatory when detecting suicidal/self-harm intent
@tool
def suicide_related_tool(text: str) -> str:
    """
    Tool that provides a safe, supportive response for suicidal or self-harm related messages.
    """
    return (
        "I'm really sorry you're feeling this way. "
        "Your life is important and you deserve support. "
        "Please reach out immediately to someone you trust, a family member, "
        "friend, or local mental health professional. "
        "If you are in immediate danger, contact your local emergency services. "
        "You are not alone."
    )

# List of available tools for the agent to choose from
tools = [
    positive_prompt_tool,
    negative_prompt_tool,
    student_marks_tool,
    suicide_related_tool,
]

# Conversation memory to store chat history in LangChain
session_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
)

# Prompt template defining system instructions and placeholders for memory
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

# Create the LangChain agent that uses OpenAI function calling
agent = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

# AgentExecutor orchestrates execution, tool selection, and memory usage
main_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=session_memory,
    verbose=False,
    return_intermediate_steps=True,
)

# Save conversation entry to MongoDB
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

# Retrieve chat history from the database
def get_history(session_id: str):
    history = (
        conversation_collection.find({"session_id": session_id}, {"_id": 0})
        .sort("timestamp", 1)
    )
    return list(history)

# Pipeline: Sends user input through the agent and logs tool usage
def run_pipeline(user_input: str, session_id: str):
    """
    Runs the LangChain agent on user input and logs tool usage.
    """
    try:
        result = main_agent.invoke({"input": user_input})

        # Extract final output
        response = result.get("output", "")

        # Detect last tool used if any intermediate steps exist
        intermediate_steps = result.get("intermediate_steps", [])
        if intermediate_steps:
            last_action = intermediate_steps[-1][0]
            tool_used = getattr(last_action, "tool", "unknown_tool")
        else:
            tool_used = "no_tool"

    except Exception as e:
        response = f"Agent Error: {str(e)}"
        tool_used = "error"

    # Persist chat entry
    save_conversation(session_id, user_input, response, tool_used)

    return response, tool_used

# Request model for chat endpoint
class ChatRequest(BaseModel):
    session_id: str
    message: str

# API route: Chat endpoint using agent pipeline
@app.post("/chat")
async def chat(req: ChatRequest):
    response, tool_used = run_pipeline(req.message, req.session_id)

    return {
        "session_id": req.session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user": req.message,
        "response": response,
        "route_selected": tool_used,
    }

# API route: Fetch stored conversation history
@app.get("/history/{session_id}")
async def fetch_history(session_id: str):
    history = get_history(session_id)
    return {"session_id": session_id, "history": history}

# API route: Delete all conversation entries for a session
@app.delete("/reset-history/{session_id}")
async def reset_history(session_id: str):
    conversation_collection.delete_many({"session_id": session_id})
    return {"status": f"Session {session_id} history reset successfully"}

# Root endpoint returning simple status message
@app.get("/")
def home():
    return {"status": "AI Agent Backend (Auto Tool Selection) Running ✅"}
