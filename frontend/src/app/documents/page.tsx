'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { listDocuments, deleteDocument } from '@/lib/api'
import { formatBytes, formatDate } from '@/lib/utils'
import type { Document } from '@/types'

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await listDocuments()
      setDocuments(response.documents)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleDelete = async (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
      return
    }

    setDeletingId(documentId)
    setError(null)

    try {
      await deleteDocument(documentId)
      // Remove from list
      setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document')
    } finally {
      setDeletingId(null)
    }
  }

  const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return '📄'
      case 'docx':
      case 'doc':
        return '📝'
      case 'xlsx':
      case 'xls':
        return '📊'
      case 'txt':
        return '📃'
      default:
        return '📎'
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">Your Documents</h1>
          <p className="text-gray-600">
            Manage your uploaded financial documents
          </p>
        </div>
        <Button asChild>
          <a href="/upload">Upload New Document</a>
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Uploaded Documents</CardTitle>
          <CardDescription>
            {loading
              ? 'Loading documents...'
              : `${documents.length} document${documents.length !== 1 ? 's' : ''} total`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📁</div>
              <h3 className="text-lg font-medium mb-2">No documents yet</h3>
              <p className="text-sm text-gray-500 mb-4">
                Upload your first financial document to get started
              </p>
              <Button asChild>
                <a href="/upload">Upload Document</a>
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-4 flex-1 min-w-0">
                    <div className="text-4xl flex-shrink-0">
                      {getFileIcon(doc.file_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate">{doc.filename}</h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                        <span className="uppercase">{doc.file_type}</span>
                        <span>•</span>
                        <span>{formatBytes(doc.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(doc.upload_date)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(doc.document_id, doc.filename)}
                      disabled={deletingId === doc.document_id}
                    >
                      {deletingId === doc.document_id ? 'Deleting...' : 'Delete'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Card */}
      {documents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-2xl font-bold">{documents.length}</div>
                <div className="text-sm text-gray-500">Total Documents</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {formatBytes(
                    documents.reduce((sum, doc) => sum + doc.file_size, 0)
                  )}
                </div>
                <div className="text-sm text-gray-500">Total Size</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {new Set(documents.map((d) => d.file_type)).size}
                </div>
                <div className="text-sm text-gray-500">File Types</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {documents.length > 0
                    ? formatDate(
                        Math.max(...documents.map((d) => new Date(d.upload_date).getTime()))
                      )
                    : 'N/A'}
                </div>
                <div className="text-sm text-gray-500">Last Upload</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Document Management</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-600">
          <p>• Documents are processed and stored as vector embeddings for fast semantic search</p>
          <p>• Deleting a document removes both the file and its vector embeddings</p>
          <p>• Supported formats: PDF, DOCX, XLSX, TXT (max 50MB)</p>
          <p>• You can query all your documents at once from the Chat page</p>
        </CardContent>
      </Card>
    </div>
  )
}
