# Resume Builder Agent - Project Overview for Claude

**Last Updated:** October 2, 2025
**Status:** Frontend Development Phase

---

## 📋 Project Summary

An AI-powered resume builder that uses **LangGraph** + **OpenAI** to create ATS-optimized resumes tailored to specific job descriptions.

**Architecture:**
- **Backend:** FastAPI + LangGraph + SQLite + Firebase Auth
- **Frontend:** Next.js 15 + TypeScript + Tailwind CSS + Firebase Auth
- **AI Workflow:** LangGraph stateful agent with profile extraction, job analysis, content selection, and ATS optimization

---

## 🎯 Current Status

### ✅ Completed

**Backend (FastAPI + LangGraph):**
- ✅ LangGraph workflow with 6 nodes (greeting, profile extraction, job analysis, content selection, ATS optimization, resume generation)
- ✅ Firebase authentication middleware
- ✅ Multi-user support with user isolation
- ✅ SQLite database (profiles, resume generations, conversations)
- ✅ API endpoints for chat, resumes, and user management
- ✅ LaTeX/PDF generation service
- ✅ Thread-based conversation state management
- ✅ Complete backend testing via test_flow.py

**Frontend Structure:**
- ✅ Next.js 15 app with TypeScript
- ✅ Tailwind CSS configured
- ✅ Firebase client SDK setup
- ✅ Auth context provider with Google + Email/Password auth
- ✅ API client with Firebase token interceptor
- ✅ Landing page (app/page.tsx)
- ✅ Login/Register page (app/login/page.tsx)
- ✅ Dashboard page (app/dashboard/page.tsx)
- ✅ Builder/Chat page (app/builder/page.tsx)
- ✅ Navbar component
- ✅ All dependencies installed (firebase, axios, etc.)

### 🚧 In Progress / To Complete

**Frontend Issues to Fix:**
- ❌ Missing .env.local file (Firebase config not set up)
- ❌ Resume detail page ([id]/page.tsx) appears to be missing or incomplete
- ❌ Firebase import error in lib/firebase.ts (line 1: importing from 'firebase/auth' instead of 'firebase/app')
- ⚠️ Need to test integration with backend API
- ⚠️ Need to verify all API endpoints work from frontend
- ⚠️ May need PDF viewer component for resume viewing

**Deployment:**
- ❌ Backend not deployed to production
- ❌ Frontend not deployed to Vercel/Netlify
- ❌ Firebase project needs to be configured

---

## 🏗️ Architecture Overview

### Backend API Structure
\`\`\`
src/
├── api/
│   ├── main.py              # FastAPI app entry point
│   ├── dependencies.py      # Dependency injection
│   ├── firebase_auth.py     # Firebase auth middleware
│   └── routers/
│       ├── auth.py          # /api/auth/login
│       ├── chat.py          # /api/chat/message (main LangGraph invocation)
│       └── resumes.py       # /api/resumes/* (CRUD operations)
└── resume_agent/
    ├── graph.py             # LangGraph workflow definition
    ├── nodes.py             # All agent nodes
    ├── latex_service.py     # PDF generation
    ├── database.py          # SQLite operations
    └── models.py            # Pydantic models
\`\`\`

### Frontend Structure
\`\`\`
frontend/
├── app/
│   ├── page.tsx             # Landing page
│   ├── layout.tsx           # Root layout with AuthProvider + Navbar
│   ├── login/page.tsx       # Authentication page
│   ├── dashboard/page.tsx   # Resume list view
│   ├── builder/page.tsx     # Chat interface
│   └── resume/[id]/         # Resume detail view (NEEDS COMPLETION)
├── components/
│   └── Navbar.tsx           # Navigation component
├── contexts/
│   └── AuthContext.tsx      # Firebase auth state management
└── lib/
    ├── firebase.ts          # Firebase initialization (HAS BUG)
    └── api.ts               # API client with auth interceptor
\`\`\`

### LangGraph Workflow
\`\`\`
User Input → Greeting Node
           ↓
     Profile Extraction → Save to DB
           ↓
     Job Analysis
           ↓
     Content Selection (ranks experiences)
           ↓
     ATS Optimization (keyword matching)
           ↓
     Resume Generation (LaTeX → PDF)
           ↓
     Save to DB + Return
\`\`\`

---

## 🔥 Firebase Configuration

### Required Environment Variables

**Backend (.env in root):**
\`\`\`bash
OPENAI_API_KEY=sk-...
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=...
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/...
\`\`\`

**Frontend (.env.local in frontend/):** ⚠️ **NEEDS TO BE CREATED**
\`\`\`bash
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456:web:abc123

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
\`\`\`

---

## 🚀 How to Run

### Backend
\`\`\`bash
# Install dependencies
pip install -e .

# Run FastAPI server
python -m src.api.main

# OR run with LangGraph Studio
langgraph dev
\`\`\`

Backend runs on: http://localhost:8000
LangGraph Studio: http://localhost:2024

### Frontend
\`\`\`bash
cd frontend

# Install dependencies (if not done)
npm install

# Run dev server
npm run dev
\`\`\`

Frontend runs on: http://localhost:3000

---

## 🐛 Known Issues to Fix

### 1. Firebase Import Bug in lib/firebase.ts
**Current (Line 1):**
\`\`\`typescript
import { initializeApp } from 'firebase/auth'; // ❌ WRONG
\`\`\`

**Should be:**
\`\`\`typescript
import { initializeApp } from 'firebase/app'; // ✅ CORRECT
\`\`\`

### 2. Missing .env.local in Frontend
Need to create `frontend/.env.local` with Firebase config variables.

### 3. Resume Detail Page Missing
The `frontend/app/resume/[id]/` directory exists but may be missing page.tsx.

**Expected functionality:**
- Display resume details (job title, company, ATS score)
- Show LaTeX code
- Download PDF button
- Option to copy LaTeX code
- Delete resume button

---

## 📊 Database Schema

### SQLite Tables

**user_profiles**
- firebase_uid (PK)
- full_name, email, phone, linkedin, github
- education (JSON), experiences (JSON), projects (JSON), skills (JSON)
- created_at, updated_at

**resume_generations**
- id (PK)
- firebase_uid (FK)
- thread_id
- job_title, company_name
- job_description, matched_keywords
- selected_experiences (JSON), selected_projects (JSON)
- latex_code, pdf_path
- ats_score
- created_at

**user_threads**
- id (PK)
- firebase_uid (FK)
- thread_id
- last_message
- created_at, updated_at

---

## 🔗 API Endpoints

### Auth
- `POST /api/auth/login` - Firebase token verification + user creation

### Chat
- `POST /api/chat/message` - Send message to LangGraph agent
  - Body: `{ message: string, thread_id?: string }`
  - Returns: `{ response: string, thread_id: string, latex_code?: string, ats_score?: number }`

### Resumes
- `GET /api/resumes/` - Get all resumes for logged-in user
- `GET /api/resumes/{id}` - Get specific resume
- `DELETE /api/resumes/{id}` - Delete resume
- `GET /api/resumes/profile/me` - Get user profile
- `DELETE /api/resumes/profile/me` - Delete user profile

---

## 📝 Next Steps (Priority Order)

### Immediate (Must Do First)
1. **Fix Firebase import bug** in `frontend/lib/firebase.ts`
2. **Create .env.local** in frontend/ with Firebase config
3. **Create/Complete resume detail page** at `frontend/app/resume/[id]/page.tsx`
4. **Test end-to-end flow:**
   - Sign up → Dashboard → Builder → Generate Resume → View Resume
5. **Fix any API integration issues** between frontend and backend

### Short-term Improvements
6. Add PDF viewer or download functionality to resume detail page
7. Add loading states and error handling throughout frontend
8. Add toast notifications for success/error messages
9. Implement resume editing/regeneration flow
10. Add profile management page

### Deployment
11. Deploy backend to Google Cloud Run or Railway
12. Deploy frontend to Vercel
13. Update Firebase authorized domains
14. Switch to PostgreSQL for production (optional)
15. Set up proper environment variables in deployment platforms

---

## 🧪 Testing

### Backend Tests Available
- `test_auth.py` - Firebase auth verification
- `test_flow.py` - Complete resume generation flow
- `test_graph.py` - LangGraph node testing

### Frontend Testing Needed
- Manual testing of all pages
- Auth flow (sign up, login, logout)
- Resume generation flow
- CRUD operations on resumes
- Error handling and edge cases

---

## 💡 Important Notes

### User Flow
1. User visits landing page
2. Signs up/logs in with Google or Email/Password
3. Redirected to Dashboard (empty initially)
4. Clicks "New Resume" → Goes to Builder
5. Chats with AI agent:
   - Says "hi"
   - Pastes resume
   - Pastes job description
   - Gets optimized resume with ATS score
6. Views generated resume in Dashboard
7. Can click to view details, download PDF, copy LaTeX

### Authentication Flow
1. Frontend: User signs in with Firebase
2. Frontend: Gets Firebase ID token
3. Frontend: Sends token to backend `/api/auth/login`
4. Backend: Verifies token with Firebase Admin SDK
5. Backend: Creates/updates user in database
6. Frontend: Stores user in AuthContext
7. Frontend: All API calls include Firebase token in Authorization header
8. Backend: Middleware extracts firebase_uid from token for user isolation

### State Management
- **LangGraph:** Uses checkpoints in `resume_builder_checkpoints.db` to maintain conversation state per thread
- **Frontend:** Uses React Context for auth state
- **Backend:** Stateless (state stored in LangGraph checkpoints + SQLite)

---

## 📚 Documentation Files

- `README.md` - Project overview
- `QUICK_START.md` - Backend testing guide
- `DEPLOYMENT_GUIDE.md` - Full deployment instructions
- `FASTAPI_SETUP.md` - FastAPI backend setup
- `NEXTJS_SETUP.md` - Frontend setup guide
- `MULTI_USER_SUMMARY.md` - Multi-user architecture explanation
- `CONVERSATION_FIX.md` - Conversation flow details
- `NEW_GRAPH_STRUCTURE.md` - LangGraph workflow documentation

---

## 🔍 Key Files to Know

### Backend
- `src/api/main.py` - FastAPI app, CORS, routes
- `src/resume_agent/graph.py` - LangGraph workflow definition
- `src/resume_agent/nodes.py` - All agent logic (profile extraction, job analysis, etc.)
- `src/resume_agent/database.py` - All database operations

### Frontend
- `frontend/contexts/AuthContext.tsx` - Auth state + Firebase methods
- `frontend/lib/api.ts` - All API calls to backend
- `frontend/app/builder/page.tsx` - Main chat interface for resume building
- `frontend/app/dashboard/page.tsx` - Resume list view

---

## 🎨 UI/UX Features Implemented

- Responsive design with Tailwind CSS
- Clean, modern interface
- Loading states with animations
- Real-time chat interface
- ATS score visualization
- Resume card previews
- Google sign-in button with icon
- Error message displays
- Auto-scroll in chat

---

## ⚙️ Technologies Used

**Backend:**
- Python 3.11+
- FastAPI
- LangGraph (Anthropic/LangChain)
- OpenAI API (GPT-4)
- Firebase Admin SDK
- SQLite (can migrate to PostgreSQL)
- LaTeX (pdflatex) for PDF generation

**Frontend:**
- Next.js 15 (App Router)
- React 19
- TypeScript
- Tailwind CSS 4
- Firebase SDK (Auth)
- Axios

---

## 🚨 Common Pitfalls

1. **Thread ID Management:** Frontend must persist and reuse thread_id for conversation continuity
2. **Firebase Token Expiry:** Tokens expire after 1 hour - frontend handles refresh automatically
3. **LaTeX Installation:** Backend needs pdflatex installed for PDF generation (or will return LaTeX code only)
4. **CORS:** Backend has CORS enabled for localhost:3000 and localhost:2024
5. **User Isolation:** All queries must filter by firebase_uid from token

---

## 🎯 Project Goals Achieved

✅ Multi-user resume builder
✅ AI-powered profile extraction
✅ Job-specific resume optimization
✅ ATS scoring and keyword matching
✅ Professional LaTeX/PDF output
✅ Conversation-based interface
✅ User authentication and isolation
✅ Database persistence

**Next Goal:** Complete and deploy functional frontend! 🚀

---

**End of Document**
