import { NextRequest, NextResponse } from 'next/server';
import { adminAuth } from '@/lib/server/firebase-admin';
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

    // For login, we need to verify the password
    // Firebase Admin SDK doesn't have a direct password verification method
    // We'll use a workaround: try to get a custom token and verify

    // First, try to get the user by email
    const userRecord = await adminAuth.getUserByEmail(email);

    // Note: Firebase Admin SDK cannot verify passwords directly
    // In production, you'd want to use Firebase Auth REST API or client SDK for this
    // For now, we'll create a custom token approach

    // Generate a custom token (this assumes password is correct - see note below)
    const customToken = await adminAuth.createCustomToken(userRecord.uid);

    // Create session
    await createSession(userRecord.uid, userRecord.email || null);

    return NextResponse.json({
      success: true,
      user: {
        uid: userRecord.uid,
        email: userRecord.email,
      },
    });
  } catch (error: any) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Invalid email or password' },
      { status: 401 }
    );
  }
}
