# FastAPI Multi-User Backend Setup

## 🎯 Overview

The Resume Builder now supports multiple users! This guide shows you how to run the FastAPI backend that enables:

- **Firebase Authentication** (Google, email/password)
- **Multi-user support** (each user has their own profile and resumes)
- **RESTful API** for Next.js frontend
- **Streaming responses** from LangGraph

---

## 📋 Prerequisites

1. **Firebase Project** (for authentication)
2. **Python 3.11+** with venv
3. **Dependencies installed** (`pip install -e .`)

---

## 🔥 Firebase Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enable **Authentication** → **Sign-in methods**:
   - Google
   - Email/Password

### 2. Get Firebase Admin SDK Credentials

1. Go to **Project Settings** → **Service accounts**
2. Click "Generate new private key"
3. Download the JSON file (e.g., `firebase-credentials.json`)
4. **Keep this file secret!**

### 3. Set Environment Variables

Add to your `.env` file:

```bash
# Firebase Admin SDK
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
# OR as JSON string:
# FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...","private_key":"..."}'

# FastAPI Settings
PORT=8000
FRONTEND_URL=http://localhost:3000

# OpenAI (existing)
OPENAI_API_KEY=your-openai-api-key
```

---

## 🚀 Running the FastAPI Server

### Option 1: Direct Run

```bash
cd resume-builder-agent
python -m src.api.main
```

### Option 2: With Uvicorn

```bash
cd resume-builder-agent
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: **http://localhost:8000**

---

## 📡 API Endpoints

### Authentication

#### `POST /api/auth/login`
Login or register user with Firebase token

**Request:**
```json
{
  "firebase_token": "<Firebase ID token from frontend>"
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "message": "Login successful"
}
```

#### `GET /api/auth/me`
Get current user info

**Headers:**
```
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2025-10-02T12:00:00"
}
```

---

### Chat (Resume Builder)

#### `POST /api/chat/message`
Send a message to the resume builder agent

**Headers:**
```
Authorization: Bearer <firebase_token>
```

**Request:**
```json
{
  "message": "hi",
  "thread_id": "optional-thread-id"
}
```

**Response:**
```json
{
  "thread_id": "generated-or-provided-id",
  "response": "Welcome! Please paste your resume...",
  "current_stage": "waiting_for_resume",
  "ats_score": null,
  "latex_code": null,
  "pdf_path": null
}
```

#### `POST /api/chat/stream`
Stream responses (Server-Sent Events)

**Headers:**
```
Authorization: Bearer <firebase_token>
```

**Request:**
```json
{
  "message": "paste job description here",
  "thread_id": "existing-thread-id"
}
```

**Response:** Server-Sent Events stream

---

### Resumes

#### `GET /api/resumes/`
List all user's resumes

**Headers:**
```
Authorization: Bearer <firebase_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "job_title": "Software Engineer",
    "company_name": "TechCorp",
    "ats_score": 82.5,
    "created_at": "2025-10-02T12:00:00",
    "has_pdf": true
  }
]
```

#### `GET /api/resumes/{resume_id}`
Get specific resume details

**Headers:**
```
Authorization: Bearer <firebase_token>
```

**Response:**
```json
{
  "id": 1,
  "job_title": "Software Engineer",
  "company_name": "TechCorp",
  "job_description": "...",
  "ats_score": 82.5,
  "latex_code": "\\documentclass...",
  "pdf_path": "outputs/resume_123.pdf",
  "created_at": "2025-10-02T12:00:00"
}
```

#### `DELETE /api/resumes/{resume_id}`
Delete a resume

**Headers:**
```
Authorization: Bearer <firebase_token>
```

#### `GET /api/resumes/profile/me`
Get user's profile data

**Response:**
```json
{
  "has_profile": true,
  "contact": {...},
  "education": [...],
  "experience": [...],
  "projects": [...],
  "technical_skills": {...}
}
```

---

## 🧪 Testing the API

### Using curl:

```bash
# 1. Login (after getting Firebase token from frontend)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"firebase_token": "your-firebase-token"}'

# 2. Send chat message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer your-firebase-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "hi"}'

# 3. List resumes
curl -X GET http://localhost:8000/api/resumes/ \
  -H "Authorization: Bearer your-firebase-token"
```

### Using Python:

```python
import requests

# Firebase token (get from frontend after user signs in)
firebase_token = "your-firebase-token"

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"firebase_token": firebase_token}
)
user_data = response.json()
print(user_data)

# Send message
response = requests.post(
    "http://localhost:8000/api/chat/message",
    headers={"Authorization": f"Bearer {firebase_token}"},
    json={
        "message": "hi",
        "thread_id": None
    }
)
chat_response = response.json()
print(chat_response)
```

---

## 🔒 Security Notes

1. **Never commit Firebase credentials!**
   - Add `firebase-credentials.json` to `.gitignore`
   - Use environment variables in production

2. **Token Verification:**
   - Every request verifies the Firebase token
   - Invalid/expired tokens return 401 Unauthorized

3. **User Isolation:**
   - Each user can only access their own resumes
   - user_id is extracted from verified token

---

## 🐛 Troubleshooting

### Firebase Initialization Failed

**Error:** `WARNING: Firebase credentials not found. Using test mode.`

**Solution:**
1. Check `.env` has `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_CREDENTIALS_JSON`
2. Verify the JSON file exists and is valid
3. In test mode, authentication is bypassed (insecure!)

### Invalid Token Error

**Error:** `401 Unauthorized: Invalid or expired token`

**Solutions:**
1. Get a fresh Firebase ID token from frontend
2. Check Firebase project settings match
3. Verify token hasn't expired (1 hour default)

### User Not Created

**Error:** User not found in database after login

**Solution:**
- Users are auto-created on first login
- Check database connection
- Verify `resume_builder.db` exists

---

## 📊 API Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🚢 Deployment

### Docker (Coming Soon)

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### GCP Cloud Run

1. Build container
2. Set environment variables (Firebase credentials as JSON string)
3. Deploy:

```bash
gcloud run deploy resume-builder-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FIREBASE_CREDENTIALS_JSON="$(cat firebase-credentials.json)"
```

---

## ✅ Next Steps

1. **✅ Backend ready!** FastAPI server is set up for multi-user support
2. **Next:** Build Next.js frontend
3. **Then:** Connect frontend to this API
4. **Finally:** Deploy both to production

---

## 📁 File Structure

```
src/
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── firebase_auth.py        # Firebase token verification
│   ├── dependencies.py         # Auth middleware
│   └── routers/
│       ├── auth.py             # /api/auth/*
│       ├── chat.py             # /api/chat/*
│       └── resumes.py          # /api/resumes/*
└── resume_agent/
    ├── graph.py                # LangGraph workflow
    ├── nodes.py                # Multi-user support added!
    └── ...
```

---

**Questions?** Check the main `README.md` or `DEPLOYMENT_GUIDE.md`!
