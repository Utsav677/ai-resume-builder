import { NextResponse } from 'next/server';
import { getSession } from '@/lib/server/session';
import { SignJWT } from 'jose';

// This endpoint returns a signed JWT for backend API authentication
export async function GET() {
  try {
    const session = await getSession();

    if (!session) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    // Generate a JWT signed by our server
    const secret = new TextEncoder().encode(process.env.SESSION_SECRET || 'fallback-secret-key');

    const token = await new SignJWT({
      uid: session.uid,
      email: session.email
    })
      .setProtectedHeader({ alg: 'HS256' })
      .setIssuedAt()
      .setExpirationTime('24h')
      .sign(secret);

    return NextResponse.json({ token });
  } catch (error: any) {
    console.error('Token generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate token' },
      { status: 500 }
    );
  }
}
