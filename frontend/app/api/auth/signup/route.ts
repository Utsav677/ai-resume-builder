import { NextRequest, NextResponse } from 'next/server';
import { createSession } from '@/lib/server/session';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Call FastAPI backend for secure user creation
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const authResponse = await fetch(`${backendUrl}/api/auth/email/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!authResponse.ok) {
      const errorData = await authResponse.json();
      throw new Error(errorData.detail || 'Failed to create account');
    }

    const authData = await authResponse.json();

    // Create session with Firebase user data
    await createSession(authData.user.uid, authData.user.email);

    return NextResponse.json({
      success: true,
      user: {
        uid: authData.user.uid,
        email: authData.user.email,
      },
    });
  } catch (error: any) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to create account' },
      { status: 400 }
    );
  }
}
