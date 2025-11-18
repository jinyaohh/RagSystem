'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { listJobs, getJob, cancelJob } from '@/lib/api'
import { ProcessingJob, JobStatus, ProcessingStep } from '@/types'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'

const statusColors: Record<JobStatus, string> = {
  [JobStatus.QUEUED]: 'bg-gray-100 text-gray-800',
  [JobStatus.PROCESSING]: 'bg-blue-100 text-blue-800',
  [JobStatus.COMPLETED]: 'bg-green-100 text-green-800',
  [JobStatus.FAILED]: 'bg-red-100 text-red-800',
  [JobStatus.CANCELLED]: 'bg-yellow-100 text-yellow-800',
}

const stepLabels: Record<ProcessingStep, string> = {
  [ProcessingStep.QUEUED]: 'Queued',
  [ProcessingStep.EXTRACTION]: 'Extracting text',
  [ProcessingStep.CHUNKING]: 'Chunking document',
  [ProcessingStep.EMBEDDING]: 'Generating embeddings',
  [ProcessingStep.STORAGE]: 'Storing vectors',
  [ProcessingStep.COMPLETED]: 'Completed',
  [ProcessingStep.FAILED]: 'Failed',
}

export default function JobsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [jobs, setJobs] = useState<ProcessingJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pollingEnabled, setPollingEnabled] = useState(true)

  const fetchJobs = async () => {
    try {
      const response = await listJobs()
      setJobs(response.jobs)
      setError('')
    } catch (err: any) {
      setError(err.message || 'Failed to fetch jobs')
    } finally {
      setLoading(false)
    }
  }

  const handleCancelJob = async (jobId: string) => {
    try {
      await cancelJob(jobId)
      await fetchJobs()
    } catch (err: any) {
      alert(err.message || 'Failed to cancel job')
    }
  }

  const handleRefresh = async (jobId: string) => {
    try {
      const updatedJob = await getJob(jobId)
      setJobs((prevJobs) =>
        prevJobs.map((job) => (job.id === jobId ? updatedJob : job))
      )
    } catch (err: any) {
      console.error('Failed to refresh job:', err)
    }
  }

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchJobs()
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false)
    }
  }, [isAuthenticated, authLoading])

  // Poll for job updates every 3 seconds
  useEffect(() => {
    if (!isAuthenticated || !pollingEnabled) return

    const interval = setInterval(async () => {
      // Only refresh jobs that are processing or queued
      const activeJobs = jobs.filter(
        (job) => job.status === JobStatus.PROCESSING || job.status === JobStatus.QUEUED
      )

      for (const job of activeJobs) {
        await handleRefresh(job.id)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [jobs, isAuthenticated, pollingEnabled])

  if (authLoading || loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <p className="text-gray-500">Loading jobs...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Authentication Required</CardTitle>
          <CardDescription>
            Please log in to view your processing jobs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Link href="/login">
              <Button>Login</Button>
            </Link>
            <Link href="/signup">
              <Button variant="outline">Sign Up</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600">{error}</p>
          <Button onClick={fetchJobs} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Processing Jobs</h1>
          <p className="text-gray-600 mt-1">
            Monitor the status of your document processing jobs
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setPollingEnabled(!pollingEnabled)}
          >
            {pollingEnabled ? 'Pause' : 'Resume'} Auto-refresh
          </Button>
          <Button onClick={fetchJobs}>Refresh</Button>
        </div>
      </div>

      {jobs.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <p className="text-center text-gray-500">
              No processing jobs found. Upload a document to get started!
            </p>
            <div className="flex justify-center mt-4">
              <Link href="/upload">
                <Button>Upload Document</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <Card key={job.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">
                      Job {job.id.substring(0, 8)}
                    </CardTitle>
                    <CardDescription>
                      Document ID: {job.document_id.substring(0, 8)}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        statusColors[job.status]
                      }`}
                    >
                      {job.status}
                    </span>
                    {(job.status === JobStatus.PROCESSING ||
                      job.status === JobStatus.QUEUED) && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCancelJob(job.id)}
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Progress Bar */}
                {job.status === JobStatus.PROCESSING ||
                job.status === JobStatus.QUEUED ? (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">
                        {job.current_step
                          ? stepLabels[job.current_step]
                          : 'Processing...'}
                      </span>
                      <span className="font-medium">{job.progress}%</span>
                    </div>
                    <Progress value={job.progress} />
                  </div>
                ) : job.status === JobStatus.COMPLETED ? (
                  <div className="text-sm text-green-600">
                    Completed in{' '}
                    {job.completed_at &&
                      Math.round(
                        (new Date(job.completed_at).getTime() -
                          new Date(job.created_at).getTime()) /
                          1000
                      )}
                    s
                  </div>
                ) : job.status === JobStatus.FAILED ? (
                  <div className="p-3 bg-red-50 border border-red-200 rounded">
                    <p className="text-sm text-red-600">
                      {job.error_message || 'Job failed'}
                    </p>
                  </div>
                ) : null}

                {/* Timestamps */}
                <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                  <div>
                    <p className="font-medium">Created</p>
                    <p>{new Date(job.created_at).toLocaleString()}</p>
                  </div>
                  {job.started_at && (
                    <div>
                      <p className="font-medium">Started</p>
                      <p>{new Date(job.started_at).toLocaleString()}</p>
                    </div>
                  )}
                  {job.completed_at && (
                    <div>
                      <p className="font-medium">Completed</p>
                      <p>{new Date(job.completed_at).toLocaleString()}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
