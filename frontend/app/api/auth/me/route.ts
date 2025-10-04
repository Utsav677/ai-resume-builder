import { NextResponse } from 'next/server';
import { getSession } from '@/lib/server/session';

export async function GET() {
  try {
    const session = await getSession();

    if (!session) {
      return NextResponse.json({ user: null });
    }

    return NextResponse.json({
      user: {
        uid: session.uid,
        email: session.email,
      },
    });
  } catch (error: any) {
    console.error('Get user error:', error);
    return NextResponse.json({ user: null });
  }
}
