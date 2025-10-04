# Resume Builder Frontend

Next.js frontend for the AI Resume Builder with Firebase authentication.

## Setup

1. **Install dependencies:**
\`\`\`bash
npm install
\`\`\`

2. **Create `.env.local` file:**
\`\`\`bash
cp .env.local.example .env.local
\`\`\`

3. **Add your Firebase config to `.env.local`:**
\`\`\`
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456:web:abc123
NEXT_PUBLIC_API_URL=http://localhost:8000
\`\`\`

4. **Run development server:**
\`\`\`bash
npm run dev
\`\`\`

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

- 🔐 Firebase Authentication (Google + Email/Password)
- 💬 Chat interface for resume building
- 📊 Dashboard to view all resumes
- 🎯 ATS score display
- 📄 LaTeX code generation

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Auth:** Firebase Authentication
- **HTTP Client:** Axios
- **Backend:** FastAPI (see ../src/api/)

## Project Structure

\`\`\`
frontend/
├── app/
│   ├── login/          # Login page
│   ├── dashboard/      # Resume list
│   ├── builder/        # Chat interface
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Home page
│   └── globals.css     # Global styles
├── components/
│   └── Navbar.tsx      # Navigation
├── contexts/
│   └── AuthContext.tsx # Auth state
├── lib/
│   ├── firebase.ts     # Firebase config
│   └── api.ts          # API client
└── ...config files
\`\`\`

## Usage

1. **Sign in** with Google or Email/Password
2. Go to **Builder** page
3. Say "hi" to start
4. Paste your resume when asked
5. Paste job description
6. Get your ATS-optimized resume!

## Build for Production

\`\`\`bash
npm run build
npm start
\`\`\`

## Deploy to Vercel

\`\`\`bash
npm i -g vercel
vercel
\`\`\`

Remember to add environment variables in Vercel dashboard!
