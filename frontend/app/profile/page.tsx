'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

interface ProfileData {
  has_profile: boolean;
  contact: {
    full_name?: string;
    email?: string;
    phone?: string;
    linkedin?: string;
    github?: string;
    portfolio?: string;
  } | null;
  education: any[] | null;
  experience: any[] | null;
  projects: any[] | null;
  technical_skills: any | null;
}

export default function ProfilePage() {
  const { user, loading: authLoading } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (user) {
      loadProfile();
    }
  }, [user, authLoading, router]);

  const loadProfile = async () => {
    try {
      const data = await apiClient.getProfile();
      setProfile(data);
    } catch (error: any) {
      setError('Failed to load profile');
      console.error('Load profile error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProfile = async () => {
    if (!confirm('Are you sure you want to delete your profile? This will allow you to upload a new resume.')) return;

    try {
      await apiClient.deleteProfile();
      alert('Profile deleted successfully! You can now upload a new resume.');
      router.push('/dashboard');
    } catch (error) {
      alert('Failed to delete profile');
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
          <p className="text-sm text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!profile?.has_profile) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white via-gray-50 to-white">
        <div className="container mx-auto px-4 py-12">
          <div className="max-w-2xl mx-auto text-center py-20">
            <h1 className="text-3xl font-bold mb-4 text-gray-900">No Profile Yet</h1>
            <p className="text-gray-600 mb-8">
              Upload your resume in the dashboard to create your profile.
            </p>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-all"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-gray-50 to-white">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">My Profile</h1>
            <p className="text-gray-600">
              Your extracted resume information
            </p>
          </div>
          <button
            onClick={handleDeleteProfile}
            className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
          >
            Delete Profile
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {/* Contact Information */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Contact Information</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {profile.contact?.full_name && (
              <div>
                <p className="text-sm text-gray-500">Full Name</p>
                <p className="text-gray-900 font-medium">{profile.contact.full_name}</p>
              </div>
            )}
            {profile.contact?.email && (
              <div>
                <p className="text-sm text-gray-500">Email</p>
                <p className="text-gray-900 font-medium">{profile.contact.email}</p>
              </div>
            )}
            {profile.contact?.phone && (
              <div>
                <p className="text-sm text-gray-500">Phone</p>
                <p className="text-gray-900 font-medium">{profile.contact.phone}</p>
              </div>
            )}
            {profile.contact?.linkedin && (
              <div>
                <p className="text-sm text-gray-500">LinkedIn</p>
                <a href={profile.contact.linkedin} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">
                  {profile.contact.linkedin}
                </a>
              </div>
            )}
            {profile.contact?.github && (
              <div>
                <p className="text-sm text-gray-500">GitHub</p>
                <a href={profile.contact.github} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">
                  {profile.contact.github}
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Experience */}
        {profile.experience && profile.experience.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Experience</h2>
            <div className="space-y-4">
              {profile.experience.map((exp: any, idx: number) => (
                <div key={idx} className="border-l-4 border-blue-500 pl-4">
                  <h3 className="font-bold text-lg text-gray-900">{exp.title || exp.role}</h3>
                  <p className="text-gray-600">{exp.company}</p>
                  <p className="text-sm text-gray-500">{exp.duration || exp.dates}</p>
                  {exp.description && (
                    <ul className="mt-2 space-y-1 text-gray-700">
                      {Array.isArray(exp.description) ? (
                        exp.description.map((item: string, i: number) => (
                          <li key={i} className="text-sm">• {item}</li>
                        ))
                      ) : (
                        <li className="text-sm">• {exp.description}</li>
                      )}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {profile.education && profile.education.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Education</h2>
            <div className="space-y-4">
              {profile.education.map((edu: any, idx: number) => (
                <div key={idx} className="border-l-4 border-green-500 pl-4">
                  <h3 className="font-bold text-lg text-gray-900">{edu.degree}</h3>
                  <p className="text-gray-600">{edu.school || edu.institution}</p>
                  <p className="text-sm text-gray-500">{edu.year || edu.graduation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Projects */}
        {profile.projects && profile.projects.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Projects</h2>
            <div className="space-y-4">
              {profile.projects.map((proj: any, idx: number) => (
                <div key={idx} className="border-l-4 border-purple-500 pl-4">
                  <h3 className="font-bold text-lg text-gray-900">{proj.name || proj.title}</h3>
                  <p className="text-gray-700 text-sm">{proj.description}</p>
                  {proj.technologies && (
                    <p className="text-sm text-gray-600 mt-1">
                      <span className="font-medium">Technologies:</span> {Array.isArray(proj.technologies) ? proj.technologies.join(', ') : proj.technologies}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Technical Skills */}
        {profile.technical_skills && Object.keys(profile.technical_skills).length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Technical Skills</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {Object.entries(profile.technical_skills).map(([category, skills]: [string, any]) => (
                <div key={category}>
                  <p className="text-sm font-medium text-gray-500 mb-2">{category}</p>
                  <p className="text-gray-900">{Array.isArray(skills) ? skills.join(', ') : skills}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Note about editing */}
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-xl">
          <p className="font-medium">To edit your profile:</p>
          <p className="text-sm">Delete your current profile and upload an updated resume, or contact support for manual edits.</p>
        </div>
      </div>
    </div>
  );
}
