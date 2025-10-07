'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface Resume {
  id: string;  // Changed to string for UUID
  job_title: string;
  company_name: string | null;
  version: number;
  resume_filename: string;
  ats_score: number | null;
  created_at: string;
  has_pdf: boolean;
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hasProfile, setHasProfile] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user) {
      loadData();
    }
  }, [user, authLoading, router]);

  const loadData = async () => {
    try {
      // Load resumes and check profile
      const [resumesData, profileData] = await Promise.all([
        apiClient.getResumes(),
        apiClient.getProfile()
      ]);

      setResumes(resumesData);
      setHasProfile(profileData.has_profile);
    } catch (error: any) {
      setError('Failed to load data');
      console.error('Load data error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadingFile(true);
    setUploadProgress('Uploading file...');
    setError('');

    try {
      // Step 1: Upload file and extract text
      const formData = new FormData();
      formData.append('file', file);

      setUploadProgress('Extracting text from resume...');
      const uploadResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`
        },
        body: formData
      });

      if (!uploadResponse.ok) throw new Error('Upload failed');

      const uploadData = await uploadResponse.json();

      // Step 2: Send extracted text to chat to start profile extraction
      setUploadProgress('Building your profile...');
      const chatResponse = await apiClient.sendMessage(uploadData.extracted_text);

      // Step 3: Redirect to builder to continue the conversation
      setUploadProgress('Complete! Redirecting...');
      setTimeout(() => {
        router.push(`/?thread_id=${chatResponse.thread_id}`);
      }, 500);
    } catch (error) {
      setError('Failed to upload resume. Please try again.');
      console.error('Upload error:', error);
    } finally {
      setUploadingFile(false);
      setUploadProgress('');
    }
  };

  const getAuthToken = async () => {
    try {
      // Get Firebase token from our Next.js API
      const tokenResponse = await fetch('/api/auth/token');
      const data = await tokenResponse.json();
      return data.token;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;

    try {
      await apiClient.deleteResume(id);
      setResumes(resumes.filter(r => r.id !== id));
    } catch (error) {
      alert('Failed to delete resume');
    }
  };

  const handleDownload = async (id: string, filename: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resumes/${id}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`
        }
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Failed to download resume');
      console.error('Download error:', error);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
          <p className="text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-gray-50 to-white">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Your Resumes</h1>
              <p className="text-gray-600">
                Manage and track your AI-generated resumes
              </p>
            </div>
            <div className="flex items-center gap-3">
              {hasProfile && (
                <>
                  <button
                    onClick={() => router.push('/profile')}
                    className="px-6 py-3 text-gray-900 border border-gray-300 rounded-xl hover:bg-gray-50 transition-all font-medium flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    My Profile
                  </button>
                  <button
                    onClick={() => router.push('/')}
                    className="px-6 py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-all hover:scale-105 shadow-lg font-medium flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    New Resume
                  </button>
                </>
              )}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
              {error}
            </div>
          )}
        </div>

        {/* Content */}
        {resumes.length === 0 ? (
          <div className="max-w-2xl mx-auto text-center py-20">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>

            {!hasProfile ? (
              <>
                <h2 className="text-3xl font-bold mb-3 text-gray-900">
                  Welcome! Let's build your profile
                </h2>
                <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
                  Upload your existing resume to extract your profile, then create tailored resumes for any job
                </p>

                <div className="flex flex-col items-center gap-4">
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx,.txt,.tex"
                      onChange={handleFileUpload}
                      disabled={uploadingFile}
                      className="hidden"
                    />
                    <div className="px-8 py-4 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-all hover:scale-105 shadow-lg font-semibold text-lg flex items-center gap-3">
                      {uploadingFile ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          {uploadProgress || 'Uploading...'}
                        </>
                      ) : (
                        <>
                          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          Upload Resume (PDF, DOCX, LaTeX, Text)
                        </>
                      )}
                    </div>
                  </label>

                  {uploadingFile && uploadProgress && (
                    <div className="w-full max-w-md bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full animate-pulse" style={{width: '70%'}} />
                    </div>
                  )}

                  <p className="text-sm text-gray-500">
                    We'll extract your experience, education, and skills to build your profile
                  </p>
                </div>
              </>
            ) : (
              <>
                <h2 className="text-3xl font-bold mb-3 text-gray-900">
                  No resumes yet
                </h2>
                <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
                  Create your first AI-optimized resume and start landing more interviews
                </p>
                <button
                  onClick={() => router.push('/')}
                  className="px-8 py-4 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-all hover:scale-105 shadow-lg font-semibold text-lg"
                >
                  Create New Resume
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className="group bg-white rounded-2xl border border-gray-200 hover:border-blue-200 hover:shadow-xl transition-all cursor-pointer overflow-hidden"
                onClick={() => router.push(`/resume/${resume.id}`)}
              >
                {/* Header with gradient */}
                <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-600" />

                <div className="p-6">
                  {/* Title and Score */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-bold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                        {resume.job_title || 'Untitled Position'}
                      </h3>
                      {resume.company_name && (
                        <p className="text-gray-600 text-sm truncate mt-1">
                          {resume.company_name}
                        </p>
                      )}
                      {resume.resume_filename && (
                        <p className="text-gray-500 text-xs font-mono mt-1 truncate">
                          {resume.resume_filename}.pdf
                        </p>
                      )}
                    </div>
                    {resume.ats_score && (
                      <div className={`px-3 py-1.5 rounded-lg text-sm font-bold flex-shrink-0 ml-3 ${
                        resume.ats_score >= 80
                          ? 'bg-green-100 text-green-700'
                          : resume.ats_score >= 60
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-orange-100 text-orange-700'
                      }`}>
                        {resume.ats_score.toFixed(0)}%
                      </div>
                    )}
                  </div>

                  {/* Date */}
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {new Date(resume.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric'
                    })}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/resume/${resume.id}`);
                      }}
                      className="flex-1 py-2.5 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-medium"
                    >
                      View Details
                    </button>
                    {resume.has_pdf && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(resume.id, resume.resume_filename);
                        }}
                        className="p-2.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Download PDF"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(resume.id);
                      }}
                      className="p-2.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete resume"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
