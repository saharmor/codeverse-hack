'use client'

import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { open } from '@tauri-apps/api/shell'

export default function HomePage() {
  const [greeting, setGreeting] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState<'unknown' | 'connected' | 'error'>('unknown')

  useEffect(() => {
    checkBackendStatus()
  }, [])

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      if (response.ok) {
        setBackendStatus('connected')
      } else {
        setBackendStatus('error')
      }
    } catch (error) {
      setBackendStatus('error')
    }
  }

  const handleGreeting = async () => {
    setIsLoading(true)
    try {
      const result = await invoke('greet', { name: 'World' })
      setGreeting(result as string)
    } catch (error) {
      console.error('Error invoking Tauri command:', error)
      setGreeting('Error: Could not invoke Tauri command')
    } finally {
      setIsLoading(false)
    }
  }

  const openBackendDocs = () => {
    open('http://localhost:8000/docs')
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Tauri + Next.js + FastAPI
          </h1>
          <p className="text-xl text-gray-600">
            A modern desktop application with web frontend and Python backend
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Frontend</h3>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-green-700">Next.js Running</span>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Backend</h3>
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-2 ${
                backendStatus === 'connected' ? 'bg-green-500' : 
                backendStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500'
              }`}></div>
              <span className={
                backendStatus === 'connected' ? 'text-green-700' : 
                backendStatus === 'error' ? 'text-red-700' : 'text-yellow-700'
              }>
                {backendStatus === 'connected' ? 'FastAPI Connected' : 
                 backendStatus === 'error' ? 'FastAPI Error' : 'Checking...'}
              </span>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Desktop</h3>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-green-700">Tauri Active</span>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Tauri Integration */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Tauri Integration</h2>
            <p className="text-gray-600 mb-4">
              Test the native desktop integration with Tauri commands.
            </p>
            <button
              onClick={handleGreeting}
              disabled={isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Loading...' : 'Test Tauri Command'}
            </button>
            {greeting && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800">{greeting}</p>
              </div>
            )}
          </div>

          {/* Backend Integration */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">FastAPI Backend</h2>
            <p className="text-gray-600 mb-4">
              Access your Python FastAPI backend endpoints and documentation.
            </p>
            <div className="space-y-3">
              <button
                onClick={checkBackendStatus}
                className="btn-secondary w-full"
              >
                Check Backend Status
              </button>
              <button
                onClick={openBackendDocs}
                className="btn-primary w-full"
              >
                Open API Docs
              </button>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="text-center p-4">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Desktop App</h3>
              <p className="text-gray-600 text-sm">Native desktop application with Tauri</p>
            </div>

            <div className="text-center p-4">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Modern UI</h3>
              <p className="text-gray-600 text-sm">Beautiful interface with Next.js & Tailwind</p>
            </div>

            <div className="text-center p-4">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Python Backend</h3>
              <p className="text-gray-600 text-sm">Powerful API with FastAPI</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 