# MediMind – Full-Stack Medical Chatbot

An end-to-end medical chatbot built with **Angular** (frontend), **FastAPI** (backend), and **PostgreSQL** (database). Supports user registration/login, medical interviews, final assessments, and ChatGPT-style chat history.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Database Setup](#database-setup)
5. [Backend Setup](#backend-setup)
6. [Frontend Setup](#frontend-setup)
7. [Application Flow](#application-flow)
8. [Quick Start Commands](#quick-start-commands)
9. [Notes & Troubleshooting](#notes--troubleshooting)

---

## Project Overview

**MediMind** is a full-stack medical interview and diagnosis system that:
- Allows users to register and authenticate
- Conducts guided medical interviews via AI agents
- Generates final assessments with disease and severity predictions
- Maintains chat history with session management
- Provides a responsive Angular frontend with FastAPI backend

---

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **PostgreSQL 14+** (running locally or remote)
- **Angular CLI** (install globally: `npm install -g @angular/cli`)
- (Optional) **Ollama** or other LLM backend for `llm/` modules

---

## Project Structure

```
MediMind/
├── backend/
│   ├── api/                  # FastAPI routes & endpoints
│   ├── services/             # Business logic (chat, auth, history)
│   ├── database/             # Connection & SQLAlchemy models
│   ├── llm/                  # Interview & explanation agents
│   ├── rules/                # Disease engine & pattern matching
│   ├── scripts/              # RAG & hybrid search utilities
│   ├── guardrails/           # Input/output validation
│   ├── chroma_db/            # Vector database (embeddings)
│   ├── processed_chunks/     # Extracted & chunked documents
│   ├── logs/                 # Logging output
│   ├── venv/                 # Python virtual environment
│   ├── requirements.txt
│   ├── main.py
│   └── .env                  # Environment variables
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── components/
    │   │   │   ├── chatbot/       # Chat interface
    │   │   │   ├── chat-history/  # Session history sidebar
    │   │   │   └── ...
    │   │   ├── services/
    │   │   └── ...
    │   └── environments/           # API configuration
    ├── package.json
    ├── angular.json
    ├── tsconfig.json
    └── README.md
```

---

## Database Setup

### 3.1 Create Database

Open **psql** or your SQL client and run:

```sql
CREATE DATABASE "MediMind";
```

### 3.2 Create Auth Schema & User

```sql
CREATE USER auth_user WITH PASSWORD 'Medimind@123';

GRANT CONNECT ON DATABASE "MediMind" TO auth_user;

CREATE SCHEMA auth AUTHORIZATION auth_user;
GRANT USAGE, CREATE ON SCHEMA auth TO auth_user;

CREATE TABLE auth.users (
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    email VARCHAR(150) PRIMARY KEY,
    password_hash TEXT NOT NULL
);

ALTER TABLE auth.users OWNER TO auth_user;

SELECT * FROM auth.users;
```

### 3.3 Create Chat Schema & Tables

```sql
CREATE SCHEMA IF NOT EXISTS chat;

-- Chat Sessions
CREATE TABLE chat.sessions (
    session_id UUID PRIMARY KEY,
    user_email VARCHAR(150) NOT NULL REFERENCES auth.users(email) ON DELETE CASCADE,
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Chat Messages
CREATE TABLE chat.messages (
    message_id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat.sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    message_order INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Assessments (Final Diagnosis)
CREATE TABLE chat.assessments (
    assessment_id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL REFERENCES chat.sessions(session_id) ON DELETE CASCADE,
    disease VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_sessions_user_email ON chat.sessions(user_email);
CREATE INDEX idx_sessions_created_at ON chat.sessions(created_at DESC);
CREATE INDEX idx_messages_session_id ON chat.messages(session_id);
CREATE INDEX idx_messages_order ON chat.messages(session_id, message_order);

SELECT 'Chat tables created successfully!' AS status;
```

---

## Backend Setup

### 4.1 Create & Activate Virtual Environment

```bash
cd backend

# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
# source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 4.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Environment Configuration

Create `backend/.env`:

```
DATABASE_URL=postgresql://auth_user:Medimind@123@localhost:5432/MediMind
# Or with quoted password for special characters:
# DATABASE_URL=postgresql://auth_user:"Medimind@123"@localhost:5432/MediMind

# Optional LLM configuration
# OLLAMA_BASE_URL=http://localhost:11434
# MODEL_NAME=LLAMA 3.1 8B
```

### 4.4 Database Connection

The `backend/database/connection.py` should load environment variables:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")

print(f"Using DATABASE_URL: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4.5 Start Backend Server

From the `backend/` directory (with venv activated):

```bash
uvicorn api.main:app --reload
```

You should see:

```
Using DATABASE_URL: postgresql://...
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Swagger Docs:** http://127.0.0.1:8000/docs

**Available Endpoints:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/start` - Start new chat session
- `POST /api/chat/{session_id}` - Continue chat
- `GET /api/history/grouped/{email}` - Grouped chat history

---

## Frontend Setup

### 5.1 Install Dependencies

```bash
cd ../frontend

npm install

# Ensure Angular CLI is installed globally
npm install -g @angular/cli
```

### 5.2 Configure API URL

In `frontend/src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

Ensure `ChatService` uses `environment.apiUrl`.

### 5.3 Start Angular Dev Server

```bash
ng serve
# or
npm start
```

**Default URL:** http://localhost:4200

---

## Application Flow

### 6.1 Authentication

1. User **registers** via `/register` → Stored in `auth.users` with password hash
2. User **logs in** via `/login` → JWT/session token stored
3. Email used as foreign key for chat sessions

### 6.2 Chat Sessions

**Starting a Chat:**
- User sends first message → `POST /api/start`
- Backend creates session in `chat.sessions`
- Initial messages inserted into `chat.messages`
- Returns `session_id` and first assistant reply

**Continuing Chat:**
- Subsequent messages → `POST /api/chat/{session_id}`
- Uses in-memory `_sessions` and interview agent
- Saves messages to `chat.messages`
- On restart, restores from DB if `restore_session_from_db` implemented

**Interview Completion:**
- Final assessment written to `chat.assessments`
- Session status marked as `'completed'`

### 6.3 Chat History Sidebar

- `GET /api/history/grouped/{email}` returns sessions grouped by: today, yesterday, this_week, this_month, older
- Click session → `GET /api/history/conversation/{sessionId}`
- If `status = 'active'` → Can continue chat
- If `status = 'completed'` → Read-only with final assessment

---

## Quick Start Commands

### Backend

```bash
cd backend

# Setup & run
python -m venv venv
venv\Scripts\activate              # Windows
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend

npm install
ng serve
# or npm start
```

### PostgreSQL (psql)

```sql
-- Connect
\c "MediMind";

-- Check users
SELECT * FROM auth.users;

-- Check sessions
SELECT * FROM chat.sessions ORDER BY created_at DESC;

-- Check messages for a session
SELECT * FROM chat.messages WHERE session_id = '<your-session-uuid>' ORDER BY message_order;

-- Check assessments
SELECT * FROM chat.assessments;
```

---

## Notes & Troubleshooting

### Important Reminders

- Always start **PostgreSQL** before running the backend
- Restart backend after changing `.env` file
- Use a strong password in production

### Session Not Found Errors

If you see "Session not found" after backend restart:
1. Ensure `restore_session_from_db()` is implemented in `chat_service.py`
2. Verify session exists in `chat.sessions` with `status = 'active'`

**Last Updated:** December 2025
