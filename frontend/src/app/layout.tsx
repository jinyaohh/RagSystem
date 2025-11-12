import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: process.env.NEXT_PUBLIC_APP_NAME || 'Financial RAG System',
  description: 'Query financial reports using natural language',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="border-b bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center">
                  <Link href="/" className="text-xl font-bold text-primary">
                    {process.env.NEXT_PUBLIC_APP_NAME || 'Financial RAG'}
                  </Link>
                </div>

                <nav className="flex gap-4">
                  <Link href="/">
                    <Button variant="ghost">Home</Button>
                  </Link>
                  <Link href="/upload">
                    <Button variant="ghost">Upload</Button>
                  </Link>
                  <Link href="/chat">
                    <Button variant="ghost">Chat</Button>
                  </Link>
                  <Link href="/documents">
                    <Button variant="ghost">Documents</Button>
                  </Link>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="border-t bg-white mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <p className="text-center text-sm text-gray-500">
                Financial RAG System - Powered by FastAPI + Next.js
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
