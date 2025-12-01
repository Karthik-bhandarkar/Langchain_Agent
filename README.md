# AI Agent System — FastAPI + LangChain + MongoDB + Streamlit

This is an end-to-end AI Agent system built using:

- FastAPI backend  
- LangChain OpenAI Functions Agent  
- MongoDB for storing conversation history  
- Streamlit frontend for an interactive chat interface  

The system supports multiple tools, safe responses, tool-based routing, and persistent chat history per session.

## Features

### Backend
- FastAPI server exposing REST endpoints  
- LangChain OpenAI Function-Calling Agent  
- Automatic tool selection based on user intent  
- MongoDB persistent storage for conversation history  

### Tools Supported
- Marks Tool – Retrieve a student's marks and grade  
- Positive Tool – Encouraging emotional responses  
- Negative Tool – Exclusion-style or negative prompt formatting  
- Safety Tool – Safe responses for suicidal or self-harm queries  

### Frontend
- Streamlit chat interface  
- Session-specific conversation history  
- Displays which tool the agent selected  
- Reset conversation history  
- Auto-load messages from backend  

## Project Structure

main.py             # FastAPI backend, agent, tools, MongoDB logic  
streamlit_app.py    # Streamlit frontend  
requirements.txt    # Dependencies  
.env                # Environment variables  
README.md           # Documentation  

## System Architecture

![System Flowchart](assets/flowchart.png)


## Tech Stack

- Backend: FastAPI, LangChain  
- Frontend: Streamlit  
- Database: MongoDB Atlas  
- Language: Python 3.8+  
- Model: OpenAI GPT-4o-mini  

## API Endpoints

### POST `/chat`
Send a user message to the agent.

Request:
```json
{
  "session_id": "abc12345",
  "message": "What are Priya's Science marks?"
}
```

Response:
```json
{
  "session_id": "abc12345",
  "timestamp": "2025-11-23T12:30:21",
  "user": "What are Priya's Science marks?",
  "response": "Priya scored 95 in Science (Grade: A+).",
  "route_selected": "student_marks_tool"
}
```

### GET `/history/{session_id}`
Returns stored chat history for a session.

### DELETE `/reset-history/{session_id}`
Deletes all stored messages for a session.

### GET `/`
Simple health check.

## MongoDB Storage Structure

Database: `agent_db`

Collection: `conversations`  
Example:
```json
{
  "session_id": "abc12345",
  "user": "Hello",
  "assistant": "Hi there!",
  "tool_used": "positive_prompt_tool",
  "timestamp": { "$date": "2025-11-23T12:30:21Z" }
}
```

## Environment Setup

### 1. Create and activate virtual environment

Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```
OPENAI_API_KEY=your_openai_key
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/agent_db
```

## Run Backend

```bash
uvicorn main:app --reload
```

Backend URL: http://127.0.0.1:8000  
Swagger docs: http://127.0.0.1:8000/docs  

## Run Streamlit Frontend

```bash
streamlit run streamlit_app.py
```

Streamlit URL: http://localhost:8501  

## Reset Session History

```http
DELETE /reset-history/{session_id}
```

## How the System Works (Flow)

1. User sends a message  
2. Backend forwards the message to the LangChain agent  
3. Agent selects a tool (if needed) based on user intent  
4. Tool runs and returns data  
5. Agent outputs final response  
6. Backend stores user + assistant + tool name in MongoDB  
7. Frontend displays response and tool used  

## Next Steps

- Add more tools  
- Deploy application online  
- Modularize backend into multiple Python files  
- Add authentication for APIs  
