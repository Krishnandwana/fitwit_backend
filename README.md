# FitWit Backend API

FastAPI backend for the FitWit calorie and weight tracking application.

## Features

- User authentication (JWT)
- Food tracking with barcode scanning (OpenFoodFacts)
- Food weight OCR using Gemini Vision
- Body weight tracking with OCR support
- Streak calculation for consecutive logging days
- AI nutrition chatbot powered by Gemini Pro
- Android widget data endpoint
- Weight history with statistics and trends

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and update the values:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/fitwit
# Or use SQLite for development:
# DATABASE_URL=sqlite:///./fitwit.db

# Security (generate a secure key)
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Gemini API
GEMINI_API_KEY=your-gemini-api-key-here

# App Settings
APP_NAME=FitWit
DEBUG=True
```

### 3. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Or let FastAPI create tables automatically (for development)
# Tables will be created on first run
```

### 4. Run Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (form data)
- `POST /api/auth/login-json` - Login (JSON)
- `GET /api/auth/me` - Get current user

### Food
- `POST /api/food/search` - Search food by name
- `POST /api/food/barcode` - Search food by barcode
- `POST /api/food/manual` - Create food manually
- `POST /api/food/ocr-weight` - Extract weight from kitchen scale image
- `POST /api/food/log` - Log food consumption
- `GET /api/food/logs` - Get food logs (optional date param)
- `DELETE /api/food/log/{log_id}` - Delete food log

### Weight
- `POST /api/weight/manual` - Log body weight manually
- `POST /api/weight/ocr` - Extract weight from scale image
- `GET /api/weight/history` - Get weight history (optional days param: 7, 30, 90)
- `GET /api/weight/latest` - Get latest weight
- `DELETE /api/weight/{log_id}` - Delete weight log

### Streak
- `GET /api/streak` - Get current streak with motivation

### Chat
- `POST /api/chat` - Chat with AI nutrition coach

### Widget
- `GET /api/widget` - Get widget data (calories consumed/remaining)

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## OCR Features

### Food Weight OCR
Upload image of kitchen scale → Gemini Vision extracts weight in grams

**Supported formats:** JPG, PNG
**Expected output:** Weight in grams with confidence level

### Body Weight OCR
Upload image of weighing scale → Gemini Vision extracts body weight in kg

**Supported formats:** JPG, PNG
**Expected output:** Weight in kg with confidence level

## Streak Logic

A day counts as "active" if user logs:
- Body weight OR
- Food/calories

The streak is calculated as consecutive active days from today backwards.

**Motivational messages:**
- "Go dawg!"
- "You showed up again."
- "Consistency > talent."
- "Keep stacking wins."
- And more based on streak length

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/       # API endpoints
│   │   └── deps.py       # Dependencies (auth, etc.)
│   ├── core/             # Core logic (security, streak)
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # External services (Gemini, OpenFoodFacts)
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── requirements.txt
└── .env
```

## External APIs

- **OpenFoodFacts:** Barcode lookup and food database
- **Gemini Vision API:** OCR for food and body weight
- **Gemini Pro API:** AI nutrition chatbot
