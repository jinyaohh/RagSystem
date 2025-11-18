'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'
import {
  getUserAnalyticsStats,
  getUserActivity,
  getPopularQueries,
} from '@/lib/api'
import type {
  UserAnalyticsStats,
  UserActivityResponse,
  PopularQueriesResponse,
} from '@/types'
import Link from 'next/link'
import { LineChart, Line, PieChart, Pie, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { formatBytes } from '@/lib/utils'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']

export default function AnalyticsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [stats, setStats] = useState<UserAnalyticsStats | null>(null)
  const [activity, setActivity] = useState<UserActivityResponse | null>(null)
  const [popularQueries, setPopularQueries] = useState<PopularQueriesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [period, setPeriod] = useState('30d')

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      const [statsData, activityData, queriesData] = await Promise.all([
        getUserAnalyticsStats(30),
        getUserActivity(period),
        getPopularQueries(10),
      ])

      setStats(statsData)
      setActivity(activityData)
      setPopularQueries(queriesData)
      setError('')
    } catch (err: any) {
      setError(err.message || 'Failed to fetch analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      fetchAnalytics()
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false)
    }
  }, [isAuthenticated, authLoading, period])

  if (authLoading || loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <p className="text-gray-500">Loading analytics...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Authentication Required</CardTitle>
          <CardDescription>
            Please log in to view your analytics dashboard
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
          <Button onClick={fetchAnalytics} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  // Prepare chart data
  const documentTypeData = stats ? [
    { name: 'PDF', value: stats.documents_by_type.pdf },
    { name: 'DOCX', value: stats.documents_by_type.docx },
    { name: 'XLSX', value: stats.documents_by_type.xlsx },
    { name: 'TXT', value: stats.documents_by_type.txt },
  ].filter(item => item.value > 0) : []

  const activityChartData = activity?.daily_queries.map((item, index) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    queries: item.count,
    uploads: activity.daily_uploads[index]?.count || 0,
  })) || []

  const mostQueriedDocsData = stats?.most_queried_documents.map(doc => ({
    name: doc.filename.length > 20 ? doc.filename.substring(0, 20) + '...' : doc.filename,
    queries: doc.query_count,
  })) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Insights into your document usage and query patterns
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <Button onClick={fetchAnalytics} variant="outline">
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Documents</CardDescription>
            <CardTitle className="text-3xl">{stats?.total_documents || 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-gray-500">
              {formatBytes(stats?.total_storage_bytes || 0)} storage used
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Queries</CardDescription>
            <CardTitle className="text-3xl">{stats?.total_queries || 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-green-600">
              {stats?.successful_queries || 0} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Avg Response Time</CardDescription>
            <CardTitle className="text-3xl">
              {stats ? (stats.avg_query_time_ms / 1000).toFixed(1) : 0}s
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-gray-500">
              Per query
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Success Rate</CardDescription>
            <CardTitle className="text-3xl">
              {stats && stats.total_queries > 0
                ? ((stats.successful_queries / stats.total_queries) * 100).toFixed(0)
                : 0}%
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-gray-500">
              {stats?.failed_queries || 0} failed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Activity Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Over Time</CardTitle>
          <CardDescription>Daily queries and document uploads</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={activityChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="queries" stroke="#8884d8" strokeWidth={2} name="Queries" />
              <Line type="monotone" dataKey="uploads" stroke="#82ca9d" strokeWidth={2} name="Uploads" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Documents and Popular Docs Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Documents by Type */}
        <Card>
          <CardHeader>
            <CardTitle>Documents by Type</CardTitle>
            <CardDescription>Breakdown of your document formats</CardDescription>
          </CardHeader>
          <CardContent>
            {documentTypeData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={documentTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {documentTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500">
                No documents uploaded yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Most Queried Documents */}
        <Card>
          <CardHeader>
            <CardTitle>Most Queried Documents</CardTitle>
            <CardDescription>Documents you ask about most</CardDescription>
          </CardHeader>
          <CardContent>
            {mostQueriedDocsData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={mostQueriedDocsData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={120} />
                  <Tooltip />
                  <Bar dataKey="queries" fill="#8884d8" name="Queries" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center text-gray-500">
                No query data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Popular Questions */}
      <Card>
        <CardHeader>
          <CardTitle>Popular Questions</CardTitle>
          <CardDescription>Your most frequently asked questions</CardDescription>
        </CardHeader>
        <CardContent>
          {popularQueries && popularQueries.queries.length > 0 ? (
            <div className="space-y-3">
              {popularQueries.queries.map((query, index) => (
                <div
                  key={index}
                  className="flex items-start justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="font-medium text-sm">
                      {index + 1}. {query.question}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Asked {query.count} time{query.count !== 1 ? 's' : ''} •{' '}
                      Avg response: {(query.avg_response_time_ms / 1000).toFixed(1)}s
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-500 py-8">
              No queries yet. Start asking questions about your documents!
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
