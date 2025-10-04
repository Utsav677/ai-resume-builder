'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

interface Resume {
  id: number;
  firebase_uid: string;
  thread_id: string;
  job_title: string;
  company_name: string | null;
  job_description: string;
  matched_keywords: string[];
  selected_experiences: any[];
  selected_projects: any[];
  latex_code: string;
  pdf_path: string | null;
  ats_score: number | null;
  created_at: string;
}

export default function ResumePage() {
  const params = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [showLatex, setShowLatex] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user && params.id) {
      loadResume();
    }
  }, [user, authLoading, params.id, router]);

  const loadResume = async () => {
    try {
      const data = await apiClient.getResume(Number(params.id));
      setResume(data);
    } catch (error: any) {
      setError('Failed to load resume');
      console.error('Load resume error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyLatex = () => {
    if (resume?.latex_code) {
      navigator.clipboard.writeText(resume.latex_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadPDF = () => {
    if (resume?.pdf_path) {
      window.open(`${process.env.NEXT_PUBLIC_API_URL}/${resume.pdf_path}`, '_blank');
    } else {
      alert('PDF not available. Please copy the LaTeX code and compile it manually.');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this resume?')) return;

    try {
      await apiClient.deleteResume(Number(params.id));
      router.push('/dashboard');
    } catch (error) {
      alert('Failed to delete resume');
    }
  };

  if (authLoading || loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  if (error || !resume) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || 'Resume not found'}
        </div>
        <button
          onClick={() => router.push('/dashboard')}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.push('/dashboard')}
          className="text-blue-600 hover:text-blue-800 mb-4"
        >
          ← Back to Dashboard
        </button>

        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {resume.job_title || 'Resume'}
            </h1>
            {resume.company_name && (
              <p className="text-xl text-gray-600 mt-1">{resume.company_name}</p>
            )}
            <p className="text-sm text-gray-500 mt-2">
              Created {new Date(resume.created_at).toLocaleString()}
            </p>
          </div>

          {resume.ats_score !== null && (
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="text-sm text-gray-600 mb-1">ATS Score</div>
              <div className="text-4xl font-bold text-green-600">
                {resume.ats_score.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {resume.ats_score >= 80
                  ? 'Excellent match!'
                  : resume.ats_score >= 60
                  ? 'Good match'
                  : 'Needs improvement'}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={handleDownloadPDF}
          className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
        >
          📥 Download PDF
        </button>
        <button
          onClick={handleCopyLatex}
          className="flex-1 bg-gray-100 hover:bg-gray-200 px-6 py-3 rounded-lg transition-colors font-semibold"
        >
          {copied ? '✓ Copied!' : '📋 Copy LaTeX'}
        </button>
        <button
          onClick={() => setShowLatex(!showLatex)}
          className="flex-1 bg-gray-100 hover:bg-gray-200 px-6 py-3 rounded-lg transition-colors font-semibold"
        >
          {showLatex ? '👁️ Hide Code' : '👁️ View Code'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Description */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-3">Job Description</h2>
            <div className="text-gray-700 whitespace-pre-wrap text-sm">
              {resume.job_description}
            </div>
          </div>

          {/* LaTeX Code */}
          {showLatex && resume.latex_code && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-3">LaTeX Code</h2>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-xs">
                <code>{resume.latex_code}</code>
              </pre>
            </div>
          )}

          {/* Selected Content */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Selected Content</h2>

            {resume.selected_experiences && resume.selected_experiences.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  Experiences ({resume.selected_experiences.length})
                </h3>
                <div className="space-y-3">
                  {resume.selected_experiences.map((exp: any, idx: number) => (
                    <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                      <div className="font-semibold">{exp.title}</div>
                      <div className="text-sm text-gray-600">{exp.company}</div>
                      {exp.relevance_score && (
                        <div className="text-xs text-gray-500 mt-1">
                          Relevance: {exp.relevance_score.toFixed(1)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {resume.selected_projects && resume.selected_projects.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  Projects ({resume.selected_projects.length})
                </h3>
                <div className="space-y-3">
                  {resume.selected_projects.map((proj: any, idx: number) => (
                    <div key={idx} className="border-l-4 border-green-500 pl-4 py-2">
                      <div className="font-semibold">{proj.name}</div>
                      <div className="text-sm text-gray-600">{proj.technologies?.join(', ')}</div>
                      {proj.relevance_score && (
                        <div className="text-xs text-gray-500 mt-1">
                          Relevance: {proj.relevance_score.toFixed(1)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Matched Keywords */}
          {resume.matched_keywords && resume.matched_keywords.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-3">Matched Keywords</h2>
              <div className="flex flex-wrap gap-2">
                {resume.matched_keywords.map((keyword: string, idx: number) => (
                  <span
                    key={idx}
                    className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="font-semibold mb-2">💡 Next Steps</h3>
            <ol className="text-sm space-y-2 text-gray-700">
              <li>1. Download the PDF to submit</li>
              <li>2. Or copy LaTeX to customize further</li>
              <li>3. Use <a href="https://overleaf.com" target="_blank" className="text-blue-600 underline">Overleaf</a> to edit LaTeX</li>
            </ol>
          </div>

          {/* Danger Zone */}
          <div className="bg-red-50 rounded-lg p-6 border border-red-200">
            <h3 className="font-semibold text-red-800 mb-3">Danger Zone</h3>
            <button
              onClick={handleDelete}
              className="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
            >
              Delete Resume
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
