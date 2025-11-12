'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { queryDocuments } from '@/lib/api'
import type { QueryResponse } from '@/types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    filename: string
    page: string
    score: string
    preview: string
  }>
  stats?: {
    response_time_ms: number
    tokens_used: number
  }
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setError(null)

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      // Query the RAG system
      const response: QueryResponse = await queryDocuments({
        question,
        top_k: 5,
        include_sources: true,
      })

      // Add assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        stats: {
          response_time_ms: response.response_time_ms,
          tokens_used: response.llm_stats?.tokens_used || 0,
        },
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed')

      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
    inputRef.current?.focus()
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Chat with Your Documents</h1>
        <p className="text-gray-600">
          Ask questions about your uploaded financial documents in natural language
        </p>
      </div>

      <Card className="flex flex-col" style={{ height: 'calc(100vh - 300px)', minHeight: '500px' }}>
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Conversation</CardTitle>
              <CardDescription>
                {messages.length === 0
                  ? 'Start by asking a question'
                  : `${messages.filter((m) => m.role === 'user').length} questions asked`}
              </CardDescription>
            </div>
            {messages.length > 0 && (
              <Button variant="outline" size="sm" onClick={clearChat}>
                Clear Chat
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-center">
              <div className="space-y-4">
                <div className="text-6xl">💬</div>
                <div>
                  <h3 className="text-lg font-medium">No messages yet</h3>
                  <p className="text-sm text-gray-500 mt-2">
                    Try asking questions like:
                  </p>
                  <ul className="text-sm text-gray-500 mt-2 space-y-1">
                    <li>• What was the revenue in Q4?</li>
                    <li>• Summarize the risk factors</li>
                    <li>• What are the key financial metrics?</li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="font-medium text-sm mb-1">
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </div>
                    <div className="whitespace-pre-wrap">{message.content}</div>

                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="text-xs font-medium mb-2">Sources:</div>
                        <div className="space-y-2">
                          {message.sources.map((source, idx) => (
                            <div key={idx} className="text-xs bg-white/50 rounded p-2">
                              <div className="font-medium">
                                {source.filename} (Page {source.page}) - Score: {source.score}
                              </div>
                              <div className="text-gray-600 mt-1 italic">
                                {source.preview}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Stats */}
                    {message.stats && (
                      <div className="mt-2 text-xs text-gray-500">
                        {message.stats.response_time_ms}ms • {message.stats.tokens_used} tokens
                      </div>
                    )}

                    <div className="text-xs mt-2 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {loading && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-lg p-4 bg-gray-100">
                    <div className="flex items-center space-x-2">
                      <div className="animate-pulse">●</div>
                      <div className="animate-pulse delay-100">●</div>
                      <div className="animate-pulse delay-200">●</div>
                      <span className="ml-2 text-sm text-gray-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </CardContent>

        {/* Input area */}
        <div className="border-t p-4">
          {error && (
            <div className="mb-3 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input
              ref={inputRef}
              type="text"
              placeholder="Ask a question about your documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              className="flex-1"
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              {loading ? 'Sending...' : 'Send'}
            </Button>
          </form>

          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send • Questions are answered using RAG from your uploaded documents
          </p>
        </div>
      </Card>

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Tips for Better Results</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-600">
          <p>• Be specific: Instead of "revenue", ask "What was the revenue in Q4 2023?"</p>
          <p>• Ask one thing at a time for clearer answers</p>
          <p>• The assistant only knows what's in your uploaded documents</p>
          <p>• Check the sources to verify information</p>
          <p>• If you don't get good results, try rephrasing your question</p>
        </CardContent>
      </Card>
    </div>
  )
}
