import { NextResponse } from 'next/server';
import { getSession } from '@/lib/server/session';
import { adminAuth } from '@/lib/server/firebase-admin';

// This endpoint returns a Firebase custom token for the backend API
export async function GET() {
  try {
    const session = await getSession();

    if (!session) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    // Generate a custom Firebase token for the backend
    const customToken = await adminAuth.createCustomToken(session.uid);

    return NextResponse.json({ token: customToken });
  } catch (error: any) {
    console.error('Token generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate token' },
      { status: 500 }
    );
  }
}
