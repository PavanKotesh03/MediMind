# Medical Interview Chatbot API V2

This is a production-ready, modular version of the Medical Interview Chatbot API with improved structure and organization.

## Project Structure

```
api_v2/
├── main.py              # Application entry point
├── requirements.txt     # Dependencies
├── models/              # Data models and schemas
│   ├── __init__.py
│   └── schemas.py       # Pydantic models
├── services/            # Business logic
│   ├── __init__.py
│   └── chat_service.py  # Chat functionality
└── routes/              # API endpoints
    ├── __init__.py
    ├── chat_routes.py   # Chat endpoints (/chat)
    └── system_routes.py # System endpoints (/health, /)
```

## Key Improvements

### 1. Modular Architecture
- **Models**: Data validation and serialization
- **Services**: Business logic separation
- **Routes**: API endpoint organization

### 2. Endpoint Changes
- `/reply` → `/chat` (as requested)
- `/start` → `/chat/start` (consistent naming)
- All endpoints under `/api/v2` prefix

### 3. Production Features
- Better error handling
- Structured logging
- Separation of concerns
- Easier to maintain and extend

## How to Run

```bash
cd d:\Rag_op\backend\api_v2
python main.py
```

The API will be available at: http://127.0.0.1:8003

## API Endpoints

- `POST /api/v2/chat/start` - Start a new medical interview
- `POST /api/v2/chat` - Continue an existing medical interview (was `/reply`)
- `POST /api/v2/chat/reset` - Reset a medical interview session
- `GET /health` - Health check
- `GET /` - API information

## Integration with Existing System

This V2 API:
- Uses the same underlying LLM agents and retrieval system
- Maintains compatibility with existing frontend (with URL changes)
- Runs on port 8001 (different from original API on port 8000)
- Can run alongside the original API without conflicts

## Migration Notes

To use this V2 API with your frontend:

1. Change API base URL from `http://localhost:8000` to `http://localhost:8003/api/v2`
2. Change endpoint from `/reply` to `/chat`
3. All other functionality remains the same
