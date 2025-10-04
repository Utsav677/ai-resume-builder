# Next.js Frontend Setup Guide

## 🎯 Overview

This guide walks you through building the Next.js frontend for the Resume Builder.

**Features:**
- Firebase Authentication (Google + Email/Password)
- Chat interface for resume building
- Dashboard to view past resumes
- Profile management
- Real-time streaming responses

---

## 🚀 Quick Start

### 1. Create Next.js App

\`\`\`bash
npx create-next-app@latest resume-builder-frontend --typescript --tailwind --app --eslint
cd resume-builder-frontend
\`\`\`

Answer prompts:
- TypeScript: **Yes**
- ESLint: **Yes**
- Tailwind CSS: **Yes**
- `src/` directory: **Yes**
- App Router: **Yes**
- Turbopack: **No** (optional)
- Import alias: **@/***

### 2. Install Dependencies

\`\`\`bash
npm install firebase axios
npm install --save-dev @types/node
\`\`\`

---

## 🔥 Firebase Setup (Frontend)

### 1. Get Firebase Config

1. Go to Firebase Console → Project Settings
2. Under "Your apps", click "Add app" → Web
3. Copy the config object

### 2. Create `.env.local`

\`\`\`bash
# Firebase Config
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456:web:abc123

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
\`\`\`

---

## 📁 Project Structure

\`\`\`
src/
├── app/
│   ├── layout.tsx              # Root layout with nav
│   ├── page.tsx                # Landing page
│   ├── login/
│   │   └── page.tsx            # Login/Register page
│   ├── dashboard/
│   │   └── page.tsx            # Resume list
│   ├── builder/
│   │   └── page.tsx            # Chat interface
│   └── resume/
│       └── [id]/
│           └── page.tsx        # View specific resume
├── components/
│   ├── Navbar.tsx              # Navigation bar
│   ├── ChatInterface.tsx       # Resume builder chat
│   ├── ResumeCard.tsx          # Resume preview card
│   └── ProtectedRoute.tsx      # Auth guard
├── lib/
│   ├── firebase.ts             # Firebase config
│   ├── api.ts                  # API client
│   └── auth.ts                 # Auth helpers
└── contexts/
    └── AuthContext.tsx         # Auth state provider
\`\`\`

---

## 🔐 Authentication Implementation

### `src/lib/firebase.ts`

\`\`\`typescript
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
\`\`\`

### `src/contexts/AuthContext.tsx`

\`\`\`typescript
'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  User,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged
} from 'firebase/auth';
import { auth, googleProvider } from '@/lib/firebase';
import axios from 'axios';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // Get Firebase token and send to backend
        const token = await firebaseUser.getIdToken();

        // Register/login user in backend
        try {
          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
            firebase_token: token
          });
        } catch (error) {
          console.error('Backend login error:', error);
        }

        setUser(firebaseUser);
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signInWithGoogle = async () => {
    await signInWithPopup(auth, googleProvider);
  };

  const signInWithEmail = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  };

  const signUpWithEmail = async (email: string, password: string) => {
    await createUserWithEmailAndPassword(auth, email, password);
  };

  const signOut = async () => {
    await firebaseSignOut(auth);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      signInWithGoogle,
      signInWithEmail,
      signUpWithEmail,
      signOut
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
\`\`\`

### `src/lib/api.ts`

\`\`\`typescript
import axios from 'axios';
import { auth } from './firebase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with interceptor to add Firebase token
const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiClient = {
  // Chat
  sendMessage: async (message: string, threadId?: string) => {
    const response = await api.post('/api/chat/message', {
      message,
      thread_id: threadId
    });
    return response.data;
  },

  // Resumes
  getResumes: async () => {
    const response = await api.get('/api/resumes/');
    return response.data;
  },

  getResume: async (id: number) => {
    const response = await api.get(`/api/resumes/${id}`);
    return response.data;
  },

  deleteResume: async (id: number) => {
    const response = await api.delete(`/api/resumes/${id}`);
    return response.data;
  },

  // Profile
  getProfile: async () => {
    const response = await api.get('/api/resumes/profile/me');
    return response.data;
  },

  deleteProfile: async () => {
    const response = await api.delete('/api/resumes/profile/me');
    return response.data;
  }
};

export default api;
\`\`\`

---

## 🎨 Example Components

### `src/app/login/page.tsx`

\`\`\`typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { signInWithGoogle, signInWithEmail, signUpWithEmail } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const router = useRouter();

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isSignUp) {
        await signUpWithEmail(email, password);
      } else {
        await signInWithEmail(email, password);
      }
      router.push('/dashboard');
    } catch (error) {
      console.error('Auth error:', error);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      await signInWithGoogle();
      router.push('/dashboard');
    } catch (error) {
      console.error('Google sign-in error:', error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <h2 className="text-3xl font-bold text-center">
          {isSignUp ? 'Sign Up' : 'Sign In'}
        </h2>

        <form onSubmit={handleEmailAuth} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full px-4 py-2 border rounded"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full px-4 py-2 border rounded"
            required
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            {isSignUp ? 'Sign Up' : 'Sign In'}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">Or</span>
          </div>
        </div>

        <button
          onClick={handleGoogleSignIn}
          className="w-full flex items-center justify-center gap-2 border border-gray-300 py-2 rounded hover:bg-gray-50"
        >
          <img src="/google-icon.svg" alt="Google" className="w-5 h-5" />
          Sign in with Google
        </button>

        <p className="text-center text-sm">
          {isSignUp ? 'Already have an account?' : "Don't have an account?"}
          <button
            onClick={() => setIsSignUp(!isSignUp)}
            className="text-blue-600 ml-1"
          >
            {isSignUp ? 'Sign In' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  );
}
\`\`\`

### `src/app/builder/page.tsx`

\`\`\`typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

export default function BuilderPage() {
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    try {
      const response = await apiClient.sendMessage(message, threadId || undefined);

      setThreadId(response.thread_id);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);

      if (response.latex_code) {
        console.log('Resume generated! ATS Score:', response.ats_score);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setMessage('');
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Resume Builder</h1>

      <div className="bg-white rounded-lg shadow h-96 overflow-y-auto p-4 mb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`mb-4 ${
              msg.role === 'user' ? 'text-right' : 'text-left'
            }`}
          >
            <div
              className={`inline-block p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-900'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 p-3 border rounded-lg"
          rows={3}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !message.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
\`\`\`

---

## 🚀 Running the Frontend

\`\`\`bash
cd resume-builder-frontend
npm run dev
\`\`\`

Visit: **http://localhost:3000**

---

## 🔗 Connect Frontend to Backend

1. **Start FastAPI backend:** `python -m src.api.main`
2. **Start Next.js frontend:** `npm run dev`
3. **Sign in** → Chat interface will communicate with backend
4. **User isolation:** Each user sees only their own resumes!

---

## 📦 Deployment

### Vercel (Recommended)

\`\`\`bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd resume-builder-frontend
vercel
\`\`\`

Update environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL=https://your-backend-url.run.app`
- Firebase config variables

---

## ✅ Complete!

You now have:
- ✅ FastAPI backend with Firebase auth
- ✅ Next.js frontend with login
- ✅ Multi-user resume builder
- ✅ Dashboard to view resumes

**Next:** Deploy both to production! 🚀
