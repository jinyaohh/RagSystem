'use client'

import { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { uploadAndProcessDocument } from '@/lib/api'
import { formatBytes } from '@/lib/utils'
import type { DocumentProcessingResult } from '@/types'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<DocumentProcessingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setResult(null)
      setError(null)
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setProgress(0)
    setError(null)
    setResult(null)

    try {
      // Simulate progress (since we don't have real progress from fetch)
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90))
      }, 500)

      const response = await uploadAndProcessDocument(file)

      clearInterval(progressInterval)
      setProgress(100)
      setResult(response)

      if (response.status === 'failed') {
        setError(response.error || 'Processing failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const resetForm = () => {
    setFile(null)
    setProgress(0)
    setResult(null)
    setError(null)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Upload Document</h1>
        <p className="text-gray-600">
          Upload a financial document to query it with natural language
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select File</CardTitle>
          <CardDescription>
            Supported formats: PDF, DOCX, XLSX, TXT (Max 50MB)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag and Drop Area */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-primary bg-primary/5'
                : 'border-gray-300 hover:border-gray-400'
            } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {file ? (
              <div className="space-y-2">
                <p className="text-lg font-medium">{file.name}</p>
                <p className="text-sm text-gray-500">{formatBytes(file.size)}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetForm}
                  disabled={uploading}
                >
                  Change File
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <p className="text-lg font-medium">
                    Drag and drop your file here
                  </p>
                  <p className="text-sm text-gray-500">or</p>
                </div>
                <div>
                  <input
                    type="file"
                    id="file-input"
                    className="hidden"
                    onChange={handleFileChange}
                    accept=".pdf,.docx,.xlsx,.txt"
                  />
                  <label htmlFor="file-input">
                    <Button variant="outline" asChild>
                      <span>Browse Files</span>
                    </Button>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Processing document...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}

          {/* Upload Button */}
          {file && !result && (
            <Button
              className="w-full"
              onClick={handleUpload}
              disabled={uploading}
              size="lg"
            >
              {uploading ? 'Processing...' : 'Upload and Process'}
            </Button>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Success Result */}
          {result && result.status === 'completed' && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded space-y-3">
              <p className="font-medium">✓ Document processed successfully!</p>

              <div className="grid grid-cols-2 gap-4 text-sm">
                {result.extraction && (
                  <div>
                    <p className="font-medium">Extracted Text</p>
                    <p>{result.extraction.text_length.toLocaleString()} characters</p>
                  </div>
                )}

                {result.chunking && (
                  <div>
                    <p className="font-medium">Chunks Created</p>
                    <p>{result.chunking.num_chunks} chunks</p>
                  </div>
                )}

                {result.embedding && (
                  <div>
                    <p className="font-medium">Embeddings</p>
                    <p>{result.embedding.model}</p>
                  </div>
                )}

                {result.storage && (
                  <div>
                    <p className="font-medium">Vectors Stored</p>
                    <p>{result.storage.num_stored} vectors</p>
                  </div>
                )}
              </div>

              <div className="pt-2">
                <Button variant="outline" onClick={resetForm} className="mr-2">
                  Upload Another
                </Button>
                <Button asChild>
                  <a href="/chat">Ask Questions</a>
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>How it works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-600">
          <p>1. Upload your financial document (PDF, DOCX, XLSX, or TXT)</p>
          <p>2. The system extracts text and breaks it into searchable chunks</p>
          <p>3. Each chunk is converted to vector embeddings using AI</p>
          <p>4. Vectors are stored in a database for fast semantic search</p>
          <p>5. You can then query the document using natural language</p>
        </CardContent>
      </Card>
    </div>
  )
}
