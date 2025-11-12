'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { detailedHealthCheck } from '@/lib/api'
import type { HealthResponse } from '@/types'

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await detailedHealthCheck()
        setHealth(data)
      } catch (error) {
        console.error('Failed to fetch health status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHealth()
  }, [])

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900">
          Financial Reports RAG System
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Upload financial documents and query them using natural language.
          Get accurate answers with source citations powered by AI.
        </p>

        <div className="flex gap-4 justify-center pt-4">
          <Link href="/upload">
            <Button size="lg">Upload Documents</Button>
          </Link>
          <Link href="/chat">
            <Button size="lg" variant="outline">
              Ask Questions
            </Button>
          </Link>
        </div>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6 pt-8">
        <Card>
          <CardHeader>
            <CardTitle>📄 Upload Documents</CardTitle>
            <CardDescription>
              Upload PDF, DOCX, Excel, or text files containing financial reports
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Our system extracts and processes text from various document formats,
              breaking them into searchable chunks with intelligent parsing.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>💬 Ask Questions</CardTitle>
            <CardDescription>
              Query your documents using natural language
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Use conversational queries to find information. Our AI retrieves
              relevant sections and generates accurate answers with citations.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>🎯 Get Answers</CardTitle>
            <CardDescription>
              Receive accurate, cited responses from your documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Every answer includes source citations with document names and page
              numbers, so you can verify the information.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Status */}
      {!loading && health && (
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>Backend services are running</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium">LLM Provider</p>
                <p className="text-gray-600">
                  {health.services?.llm.provider} - {health.services?.llm.model}
                </p>
              </div>
              <div>
                <p className="font-medium">Embedding Model</p>
                <p className="text-gray-600">
                  {health.services?.embedding.model} ({health.services?.embedding.dimension}d)
                </p>
              </div>
              <div>
                <p className="font-medium">Vector Database</p>
                <p className="text-gray-600">
                  {health.services?.vector_db.type} - {health.services?.vector_db.status}
                </p>
              </div>
              <div>
                <p className="font-medium">Document Collection</p>
                <p className="text-gray-600">
                  {health.services?.collection.vectors_count || 0} vectors stored
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-gray-500">Loading system status...</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
