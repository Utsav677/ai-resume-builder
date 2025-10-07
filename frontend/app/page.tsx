"use client"

import type React from "react"

import { useState, useRef } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  file?: File
}

export default function Home() {
  const { user } = useAuth()
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [guestResumeUploaded, setGuestResumeUploaded] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [atsScore, setAtsScore] = useState<number | null>(null)
  const [latexCode, setLatexCode] = useState<string | null>(null)
  const [pdfFilename, setPdfFilename] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const sendMessage = async (file?: File) => {
    if ((!input.trim() && !file) || loading) return

    // For file uploads, extract text from backend first
    let messageContent = input.trim()
    let fileText = ""

    if (file) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: `Uploading: ${file.name}...`,
        timestamp: new Date(),
        file,
      }

      setMessages((prev) => [...prev, userMessage])
      setLoading(true)

      try {
        // Upload file and extract text via backend
        const uploadResponse = await apiClient.uploadFile(file)
        fileText = uploadResponse.extracted_text
        messageContent = `Here's my resume:\n\n${fileText}`

        if (!user) {
          setGuestResumeUploaded(true)
        }

        // Update message to show success
        setMessages((prev) => prev.map(m =>
          m.id === userMessage.id
            ? { ...m, content: `Uploaded: ${file.name}` }
            : m
        ))

        // Clear input in case user typed something
        setInput("")

      } catch (error: any) {
        console.error("Error uploading file:", error)
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `Sorry, I couldn't process that file. ${error.response?.data?.detail || 'Please try a different format (PDF, DOCX, or TXT).'}`,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorMessage])
        setLoading(false)
        return
      }
    } else {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: "user",
        content: messageContent,
        timestamp: new Date(),
      }

      setInput("")
      setMessages((prev) => [...prev, userMessage])
      setLoading(true)
    }

    try {
      // Send message to backend API (with extracted text if from file)
      const response = await apiClient.sendMessage(messageContent, threadId || undefined)

      setThreadId(response.thread_id)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Update ATS score, LaTeX code, and PDF filename if available
      if (response.ats_score !== null && response.ats_score !== undefined) {
        setAtsScore(response.ats_score)
      }

      if (response.latex_code) {
        setLatexCode(response.latex_code)
      }

      if (response.pdf_filename) {
        setPdfFilename(response.pdf_filename)
      }

    } catch (error: any) {
      console.error("Error sending message:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again. Make sure the backend is running.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      sendMessage(file)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-screen flex-col bg-white">
      {/* Simple Header */}
      <header className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gray-900 flex items-center justify-center">
            <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <span className="text-lg font-semibold text-gray-900">Resume Builder</span>
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <button
                onClick={() => router.push("/dashboard")}
                className="px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                My Resumes
              </button>
              <div className="h-8 w-8 rounded-full bg-gray-900 flex items-center justify-center text-white text-sm font-medium">
                {user.email?.[0].toUpperCase()}
              </div>
            </>
          ) : (
            <button
              onClick={() => router.push("/login")}
              className="px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Sign in
            </button>
          )}
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-8">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="mb-6 h-16 w-16 rounded-2xl bg-gray-900 flex items-center justify-center">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h1 className="mb-3 text-3xl font-bold text-gray-900">Build your resume</h1>
              <p className="text-gray-600 mb-8 text-center max-w-md">
                {user
                  ? "Paste a job description and I'll tailor your resume to match"
                  : "Upload your resume and paste a job description to get started"}
              </p>

              <div className="grid gap-3 w-full max-w-lg">
                {!user && (
                  <>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-6 text-center hover:border-gray-400 hover:bg-gray-50 transition-colors"
                    >
                      <svg
                        className="mx-auto h-8 w-8 text-gray-400 mb-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      <div className="text-sm font-medium text-gray-900">Upload your resume</div>
                      <div className="text-xs text-gray-500 mt-1">PDF, DOC, or DOCX</div>
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </>
                )}

                {user && (
                  <button
                    onClick={() => setInput("Here's the job description I want to optimize for:\n\n")}
                    className="rounded-lg border border-gray-200 bg-white p-4 text-left hover:border-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    <div className="text-sm font-medium text-gray-900">Paste job description</div>
                    <div className="text-xs text-gray-500 mt-1">I'll tailor your resume to match</div>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <div key={message.id} className={`mb-6 flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}>
              {message.role === "assistant" && (
                <div className="h-8 w-8 shrink-0 rounded-lg bg-gray-900 flex items-center justify-center">
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === "user" ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-900"
                }`}
              >
                {message.file && (
                  <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-300">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <span className="text-xs">{message.file.name}</span>
                  </div>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>

              {message.role === "user" && (
                <div className="h-8 w-8 shrink-0 rounded-lg bg-gray-200 flex items-center justify-center">
                  <svg className="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="mb-6 flex gap-3">
              <div className="h-8 w-8 shrink-0 rounded-lg bg-gray-900 flex items-center justify-center">
                <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div className="rounded-2xl bg-gray-100 px-4 py-3">
                <div className="flex items-center gap-1">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-600" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-600 [animation-delay:0.1s]" />
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-600 [animation-delay:0.2s]" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ATS Score Display */}
      {atsScore !== null && (
        <div className="border-t border-gray-200 bg-gray-50 px-6 py-3">
          <div className="mx-auto max-w-3xl flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">ATS Score:</span>
              <div className={`px-3 py-1.5 rounded-lg text-sm font-bold ${
                atsScore >= 80
                  ? 'bg-green-100 text-green-700'
                  : atsScore >= 60
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-orange-100 text-orange-700'
              }`}>
                {atsScore.toFixed(0)}%
              </div>
            </div>
            {latexCode && (
              <div className="flex gap-2">
                {pdfFilename && !user && (
                  <a
                    href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/resumes/download/guest/${pdfFilename}`}
                    download="optimized_resume.pdf"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download PDF
                  </a>
                )}
                {user && (
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm font-medium"
                  >
                    View in Dashboard
                  </button>
                )}
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(latexCode);
                    alert('LaTeX code copied to clipboard!');
                  }}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
                >
                  Copy LaTeX
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <div className="mx-auto max-w-3xl">
          {!user && !guestResumeUploaded && messages.length > 0 && (
            <div className="mb-3 flex items-center gap-2 text-sm text-gray-600">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>Upload your resume first to get started</span>
            </div>
          )}

          <div className="relative flex gap-2">
            {!user && (
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="shrink-0 h-10 w-10 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                title="Upload resume"
              >
                <svg className="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                  />
                </svg>
              </button>
            )}

            <div className="relative flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  !user && !guestResumeUploaded
                    ? "Upload your resume first..."
                    : user
                      ? "Paste the job description..."
                      : "Paste the job description..."
                }
                className="w-full resize-none rounded-xl border border-gray-200 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent text-sm"
                rows={1}
                disabled={loading || (!user && !guestResumeUploaded)}
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || loading || (!user && !guestResumeUploaded)}
                className="absolute bottom-2 right-2 h-8 w-8 rounded-lg bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
