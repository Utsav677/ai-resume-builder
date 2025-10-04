'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, Sparkles } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function BuilderPage() {
  const { user, loading: authLoading } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [atsScore, setAtsScore] = useState<number | null>(null);
  const [latexCode, setLatexCode] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setInput('');
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await apiClient.sendMessage(userMessage.content, threadId || undefined);

      setThreadId(response.thread_id);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.ats_score !== null) {
        setAtsScore(response.ats_score);
      }

      if (response.latex_code) {
        setLatexCode(response.latex_code);
      }
    } catch (error: any) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  if (authLoading) {
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
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-border bg-background px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-lg font-semibold">AI Resume Builder</h1>
        </div>
        {atsScore !== null && (
          <div className="ml-auto flex items-center gap-2">
            <span className="text-sm text-muted-foreground">ATS Score:</span>
            <div className={`rounded-lg px-3 py-1 text-sm font-bold ${
              atsScore >= 80
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : atsScore >= 60
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
            }`}>
              {atsScore.toFixed(0)}%
            </div>
          </div>
        )}
      </header>

      {/* Messages */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="mx-auto max-w-3xl px-4 py-8">
          {messages.length === 0 && (
            <div className="flex flex-1 items-center justify-center py-16">
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <h2 className="mb-2 text-2xl font-semibold">How can I help you build your resume?</h2>
                <p className="text-muted-foreground mb-8">Start a conversation by typing a message below</p>

                <div className="grid gap-3 sm:grid-cols-2 max-w-xl mx-auto">
                  <button
                    onClick={() => setInput("Hi! I'd like to create a resume.")}
                    className="rounded-xl border border-border bg-card p-4 text-left transition-colors hover:bg-accent"
                  >
                    <div className="text-sm font-medium mb-1">Start building</div>
                    <div className="text-xs text-muted-foreground">Create a new resume</div>
                  </button>
                  <button
                    onClick={() => setInput("I want to optimize my resume for a specific job.")}
                    className="rounded-xl border border-border bg-card p-4 text-left transition-colors hover:bg-accent"
                  >
                    <div className="text-sm font-medium mb-1">Optimize resume</div>
                    <div className="text-xs text-muted-foreground">Tailor to a job</div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`mb-8 flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <Avatar className="h-8 w-8 shrink-0">
                <div
                  className={`flex h-full w-full items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground'
                  }`}
                >
                  {message.role === 'user' ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
                </div>
              </Avatar>

              {/* Message Content */}
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">
                    {message.role === 'user' ? 'You' : 'AI Assistant'}
                  </span>
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="mb-8 flex gap-4">
              <Avatar className="h-8 w-8 shrink-0">
                <div className="flex h-full w-full items-center justify-center bg-secondary text-secondary-foreground">
                  <Bot className="h-5 w-5" />
                </div>
              </Avatar>
              <div className="flex-1 space-y-2">
                <span className="text-sm font-semibold">AI Assistant</span>
                <div className="rounded-2xl bg-muted px-4 py-3">
                  <div className="flex items-center gap-1">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-foreground/40" />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-foreground/40 [animation-delay:0.1s]" />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-foreground/40 [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Actions bar (when resume is ready) */}
      {latexCode && (
        <div className="border-t border-border bg-muted/50 px-4 py-3">
          <div className="mx-auto flex max-w-3xl items-center justify-between gap-4">
            <span className="text-sm text-muted-foreground">✓ Resume generated successfully!</span>
            <div className="flex gap-2">
              <Button
                onClick={() => router.push('/dashboard')}
                variant="default"
                size="sm"
              >
                View in Dashboard
              </Button>
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(latexCode);
                  alert('LaTeX code copied!');
                }}
                variant="outline"
                size="sm"
              >
                Copy LaTeX
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border bg-background p-4">
        <div className="mx-auto max-w-3xl">
          <div className="relative flex items-end gap-2">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Message AI Resume Builder..."
              className="min-h-[52px] max-h-[200px] resize-none pr-12"
              rows={1}
              disabled={loading}
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              size="icon"
              className="absolute bottom-2 right-2 h-8 w-8"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Press Enter to send, Shift + Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
