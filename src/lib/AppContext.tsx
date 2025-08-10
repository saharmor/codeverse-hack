'use client'

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ChatMessage, Project } from './types'

interface AppContextValue {
  projects: Project[]
  selectedProjectId: string | null
  selectProject: (id: string) => void
  addProject: (project: Omit<Project, 'id'>) => void
  chatMessages: ChatMessage[]
  sendMessage: (content: string) => void
}

const AppContext = createContext<AppContextValue | undefined>(undefined)

const initialProjects: Project[] = [
  { id: 'p1', name: 'Codeverse', path: '~/codeverse', lastUpdated: '2025-08-01', icon: 'folder' },
  { id: 'p2', name: 'Marketing Site', path: '~/sites/marketing', lastUpdated: '2025-08-08', icon: 'dashboard' },
  { id: 'p3', name: 'AI Research', path: '~/work/ai-research', lastUpdated: '2025-07-24', icon: 'folder' },
]

const initialMessages: ChatMessage[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: 'Hi! I\'m ready to help. What would you like to work on today?\n\nHere are a few clarifying questions to get started:',
    timestamp: Date.now() - 1000 * 60 * 5,
  },
]

export function AppContextProvider({ children }: { children: React.ReactNode }) {
  const [projects, setProjects] = useState<Project[]>(initialProjects)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(projects[0]?.id ?? null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(initialMessages)

  const selectProject = useCallback((id: string) => {
    setSelectedProjectId(id)
  }, [])

  const addProject = useCallback((project: Omit<Project, 'id'>) => {
    const newProject: Project = { id: `p${Date.now()}`, ...project }
    setProjects(prev => [newProject, ...prev])
    setSelectedProjectId(newProject.id)
  }, [])

  const sendMessage = useCallback((content: string) => {
    const trimmed = content.trim()
    if (!trimmed) return

    const userMessage: ChatMessage = {
      id: `m${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: Date.now(),
    }

    setChatMessages(prev => [...prev, userMessage])

    // For now, simulate an assistant response immediately.
    const assistantMessage: ChatMessage = {
      id: `m${Date.now() + 1}`,
      role: 'assistant',
      content: 'Got it. I\'ll draft a plan and surface artifacts in the Task Output panel. Would you like a high-level summary or step-by-step details?',
      timestamp: Date.now(),
    }
    setChatMessages(prev => [...prev, assistantMessage])
  }, [])

  const value = useMemo<AppContextValue>(() => ({
    projects,
    selectedProjectId,
    selectProject,
    addProject,
    chatMessages,
    sendMessage,
  }), [projects, selectedProjectId, selectProject, addProject, chatMessages, sendMessage])

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useAppContext must be used within AppContextProvider')
  return ctx
}
