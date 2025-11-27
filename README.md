<<<<<<< HEAD
# AI Agent System — FastAPI + LangChain + MongoDB + Streamlit

An end-to-end example AI agent application using a FastAPI backend with a LangChain agent, persistent MongoDB memory, and a Streamlit chat UI. This repo provides session-based chat, multiple AI tools, and endpoints for history and reset.

**Features**
 - **FastAPI backend**: LangChain OpenAI Functions agent powering tool routing.
 - **MongoDB Atlas**: Persistent collections for facts and conversation history.
 - **Session-based chat**: Chat sessions tracked by `session_id` and timestamps.
 - **Multiple tools**: `Marks`, `Positive`, `Negative`, and `Mental-health Safe` tools.
 - **Streamlit frontend**: Chat UI with live history and reset capability.

**Project Structure**
 - `main.py` — FastAPI backend and agent.
 - `streamlit_app.py` — Streamlit frontend UI.
 - `requirements.txt` — Python dependencies.
 - `.env` — Environment variables (not tracked in VCS).
 - `README.md` — This file.

**Tech Stack**
 - **Backend**: FastAPI, LangChain
 - **Frontend**: Streamlit
 - **Database**: MongoDB Atlas
 - **Language**: Python 3.8+
 - **AI Model**: OpenAI GPT-4o-mini (or configured model via `OPENAI_API_KEY`)

**API Endpoints**
 - **POST** `/chat` — Chat with the AI agent. Accepts JSON with `session_id` and `message`.
 - **GET** `/history/{session_id}` — Retrieve session chat history.
 - **DELETE** `/reset-history/{session_id}` — Delete all messages for a session.
 - **GET** `/` — Health check.

Example payload for `/chat`:

```json
{
	"session_id": "abc12345",
	"message": "What are Priya's Science marks?"
}
```

Example response:

```json
{
	"session_id": "abc12345",
	"timestamp": "2025-11-23T12:30:21",
	"user": "What are Priya's Science marks?",
	"response": "Priya scored 95 in Science (Grade: A+).",
	"route_selected": "student_marks_tool"
}
```

**MongoDB Storage Structure**

Database: `agent_db`

 - Collection: `facts`
	 - Documents like: `{ "key": "name", "value": "shashank" }`

 - Collection: `conversations`
	 - Documents like:
		 ```json
		 {
			 "session_id": "abc12345",
			 "user": "...",
			 "assistant": "...",
			 "timestamp": { "$date": "2025-11-23T12:30:21Z" }
		 }
		 ```

**Tools Supported**
 - **Marks Tool**: Fetches student marks from `facts` or other sources.
 - **Positive Tool**: Generates encouraging responses.
 - **Negative Tool**: Filters or blocks unwanted prompts.
 - **Safety Tool**: Handles self-harm and sensitive keywords safely.

**Environment Setup**
1. Create and activate a virtual environment.

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

**`.env` file** (create in project root):

```
OPENAI_API_KEY=your_openai_key
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/agent_db
```

**Run the Backend**

```powershell
# Start FastAPI (from project root)
uvicorn main:app --reload

# Backend will be available at http://127.0.0.1:8000
# Swagger docs: http://127.0.0.1:8000/docs
```

**Run the Streamlit Frontend**

```powershell
streamlit run streamlit_app.py

# Streamlit UI by default: http://localhost:8501
```

**Reset Session History**

To delete all messages for a session:

```http
DELETE /reset-history/{session_id}
```

**Notes & Implementation Hints**
 - Use `pymongo` to persist conversation documents and facts.
 - Keep `session_id` generation client-side (allowing external clients to control session keys) or create an endpoint to mint session IDs with timestamps.
 - Use LangChain agents with OpenAI Functions-style tools (avoid deprecated APIs). Configure agent to pick tools based on user intent; store both user prompt and assistant routed result in `conversations`.
 - For sensitive content (self-harm), the Safety Tool should refuse and provide crisis resources instead of direct instructions.

**Example Minimal `requirements.txt`**

 - fastapi
 - uvicorn
 - streamlit
 - requests
 - python-dotenv
 - pydantic
 - pymongo[srv]
 - langchain
 - langchain-core
 - langchain-community
 - langchain-openai

**Example Flow**
 - A user sends `POST /chat` with a `session_id` and `message`.
 - Backend loads session memory from MongoDB, passes input to a LangChain OpenAI Functions agent.
 - Agent selects a tool (e.g., `Marks Tool`) and returns a response.
 - Backend stores the user message + assistant message in `conversations` and returns the assistant output to the caller.

**Where to go next**
 - Implement the FastAPI endpoints in `main.py` if not present.
 - Implement tool functions (`marks`, `positive`, `negative`, `safety`) and register them with the LangChain agent.
 - Wire the Streamlit UI in `streamlit_app.py` to call `/chat`, render history, and call `/reset-history`.


=======
# AI Agent System — FastAPI + LangChain + MongoDB + Streamlit

An end-to-end example AI agent application using a FastAPI backend with a LangChain agent, persistent MongoDB memory, and a Streamlit chat UI. This repo provides session-based chat, multiple AI tools, and endpoints for history and reset.

**Features**
 - **FastAPI backend**: LangChain OpenAI Functions agent powering tool routing.
 - **MongoDB Atlas**: Persistent collections for facts and conversation history.
 - **Session-based chat**: Chat sessions tracked by `session_id` and timestamps.
 - **Multiple tools**: `Marks`, `Positive`, `Negative`, and `Mental-health Safe` tools.
 - **Streamlit frontend**: Chat UI with live history and reset capability.

**Project Structure**
 - `main.py` — FastAPI backend and agent.
 - `streamlit_app.py` — Streamlit frontend UI.
 - `requirements.txt` — Python dependencies.
 - `.env` — Environment variables (not tracked in VCS).
 - `README.md` — This file.

**Tech Stack**
 - **Backend**: FastAPI, LangChain
 - **Frontend**: Streamlit
 - **Database**: MongoDB Atlas
 - **Language**: Python 3.8+
 - **AI Model**: OpenAI GPT-4o-mini (or configured model via `OPENAI_API_KEY`)

**API Endpoints**
 - **POST** `/chat` — Chat with the AI agent. Accepts JSON with `session_id` and `message`.
 - **GET** `/history/{session_id}` — Retrieve session chat history.
 - **DELETE** `/reset-history/{session_id}` — Delete all messages for a session.
 - **GET** `/` — Health check.

Example payload for `/chat`:

```json
{
	"session_id": "abc12345",
	"message": "What are Priya's Science marks?"
}
```

Example response:

```json
{
	"session_id": "abc12345",
	"timestamp": "2025-11-23T12:30:21",
	"user": "What are Priya's Science marks?",
	"response": "Priya scored 95 in Science (Grade: A+).",
	"route_selected": "student_marks_tool"
}
```

**MongoDB Storage Structure**

Database: `agent_db`

 - Collection: `facts`
	 - Documents like: `{ "key": "name", "value": "shashank" }`

 - Collection: `conversations`
	 - Documents like:
		 ```json
		 {
			 "session_id": "abc12345",
			 "user": "...",
			 "assistant": "...",
			 "timestamp": { "$date": "2025-11-23T12:30:21Z" }
		 }
		 ```

**Tools Supported**
 - **Marks Tool**: Fetches student marks from `facts` or other sources.
 - **Positive Tool**: Generates encouraging responses.
 - **Negative Tool**: Filters or blocks unwanted prompts.
 - **Safety Tool**: Handles self-harm and sensitive keywords safely.

**Environment Setup**
1. Create and activate a virtual environment.

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

**`.env` file** (create in project root):

```
OPENAI_API_KEY=your_openai_key
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/agent_db
```

**Run the Backend**

```powershell
# Start FastAPI (from project root)
uvicorn main:app --reload

# Backend will be available at http://127.0.0.1:8000
# Swagger docs: http://127.0.0.1:8000/docs
```

**Run the Streamlit Frontend**

```powershell
streamlit run streamlit_app.py

# Streamlit UI by default: http://localhost:8501
```

**Reset Session History**

To delete all messages for a session:

```http
DELETE /reset-history/{session_id}
```

**Notes & Implementation Hints**
 - Use `pymongo` to persist conversation documents and facts.
 - Keep `session_id` generation client-side (allowing external clients to control session keys) or create an endpoint to mint session IDs with timestamps.
 - Use LangChain agents with OpenAI Functions-style tools (avoid deprecated APIs). Configure agent to pick tools based on user intent; store both user prompt and assistant routed result in `conversations`.
 - For sensitive content (self-harm), the Safety Tool should refuse and provide crisis resources instead of direct instructions.

**Example Minimal `requirements.txt`**

 - fastapi
 - uvicorn
 - streamlit
 - requests
 - python-dotenv
 - pydantic
 - pymongo[srv]
 - langchain
 - langchain-core
 - langchain-community
 - langchain-openai

**Example Flow**
 - A user sends `POST /chat` with a `session_id` and `message`.
 - Backend loads session memory from MongoDB, passes input to a LangChain OpenAI Functions agent.
 - Agent selects a tool (e.g., `Marks Tool`) and returns a response.
 - Backend stores the user message + assistant message in `conversations` and returns the assistant output to the caller.

**Where to go next**
 - Implement the FastAPI endpoints in `main.py` if not present.
 - Implement tool functions (`marks`, `positive`, `negative`, `safety`) and register them with the LangChain agent.
 - Wire the Streamlit UI in `streamlit_app.py` to call `/chat`, render history, and call `/reset-history`.


>>>>>>> dd77fef (Your update message)
