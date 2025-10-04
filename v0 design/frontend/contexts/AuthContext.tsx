'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';

interface User {
  uid: string;
  email: string | null;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on mount
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await axios.get('/api/auth/me');
      setUser(response.data.user);
    } catch (error) {
      console.error('Auth check error:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const signInWithEmail = async (email: string, password: string) => {
    const response = await axios.post('/api/auth/login', { email, password });

    if (response.data.success) {
      setUser(response.data.user);

      // Get Firebase token for backend API and register with backend
      await registerWithBackend();
    } else {
      throw new Error(response.data.error || 'Login failed');
    }
  };

  const signUpWithEmail = async (email: string, password: string) => {
    const response = await axios.post('/api/auth/signup', { email, password });

    if (response.data.success) {
      setUser(response.data.user);

      // Get Firebase token for backend API and register with backend
      await registerWithBackend();
    } else {
      throw new Error(response.data.error || 'Signup failed');
    }
  };

  const signOut = async () => {
    await axios.post('/api/auth/logout');
    setUser(null);
  };

  const registerWithBackend = async () => {
    try {
      // Get Firebase token from our Next.js API
      const tokenResponse = await axios.get('/api/auth/token');
      const firebaseToken = tokenResponse.data.token;

      // Register with backend API
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
        firebase_token: firebaseToken
      });
    } catch (error) {
      console.error('Backend registration error:', error);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
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
