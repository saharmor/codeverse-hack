'use client'

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ChatMessage, Repository, Plan, PlanArtifact, ChatSession } from './types'
import { apiClient } from './api'

interface AppContextValue {
  // repositories
  repositories: Repository[]
  selectedRepositoryId: string | null
  selectRepository: (id: string) => void
  createRepository: (repo: { name: string; path: string; git_url?: string | null; default_branch?: string }) => Promise<void>
  deleteRepository: (id: string) => Promise<void>

  // plans
  plans: Plan[]
  selectedPlanId: string | null
  selectPlan: (id: string) => void
  createPlan: (payload: { name: string; description?: string; target_branch: string }) => Promise<void>
  deletePlan: (id: string) => Promise<void>
  updatePlanName: (planId: string, newName: string) => void

  // chat
  chatMessages: ChatMessage[]
  sendMessage: (content: string) => Promise<void>
  generatePlan: (message: string) => Promise<void>
  isLoading: boolean

  // artifacts
  artifacts: PlanArtifact[]
}

const AppContext = createContext<AppContextValue | undefined>(undefined)

export function AppContextProvider({ children }: { children: React.ReactNode }) {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<string | null>(null)

  const [plans, setPlans] = useState<Plan[]>([])
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null)

  const [chatSession, setChatSession] = useState<ChatSession | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const [artifacts, setArtifacts] = useState<PlanArtifact[]>([])

  // Initial load of repositories
  useEffect(() => {
    (async () => {
      const res = await apiClient.listRepositories()
      if (res.data) {
        // map backend fields to frontend casing if needed
        const repos: Repository[] = res.data.map((r: any) => ({
          id: r.id,
          name: r.name,
          path: r.path,
          gitUrl: r.git_url ?? null,
          defaultBranch: r.default_branch ?? 'main',
          createdAt: r.created_at,
          updatedAt: r.updated_at,
        }))
        setRepositories(repos)
        if (repos.length > 0) setSelectedRepositoryId(repos[0].id)
      }
    })()
  }, [])

  // Load plans whenever repository changes
  useEffect(() => {
    if (!selectedRepositoryId) return
    (async () => {
      const res = await apiClient.listPlans(selectedRepositoryId)
      if (res.data) {
        const mapped: Plan[] = res.data.map((p: any) => ({
          id: p.id,
          repositoryId: p.repository_id,
          name: p.name,
          description: p.description,
          targetBranch: p.target_branch,
          version: p.version,
          status: p.status,
          createdAt: p.created_at,
          updatedAt: p.updated_at,
        }))
        setPlans(mapped)
        setSelectedPlanId(mapped[0]?.id ?? null)
      }
    })()
  }, [selectedRepositoryId])

  // Load artifacts and chat when plan changes
  useEffect(() => {
    if (!selectedPlanId) {
      setArtifacts([])
      setChatSession(null)
      setChatMessages([])
      return
    }
    (async () => {
      const [art, chat] = await Promise.all([
        apiClient.listVersions(selectedPlanId),
        apiClient.getPlanChat(selectedPlanId).catch(() => ({ data: null })),
      ])
      if (art.data) {
        console.log('Raw artifacts/versions data:', art.data)
        const mapped: PlanArtifact[] = art.data.map((a: any) => ({
          id: a.id,
          planId: a.plan_id,
          content: a.content,
          artifactType: a.artifact_type || 'plan_version', // fallback for versions
          createdAt: a.created_at,
          version: a.version, // add version field from PlanVersion model
        }))
        console.log('Mapped artifacts:', mapped)
        setArtifacts(mapped)
      } else {
        console.log('No artifacts/versions data received')
        setArtifacts([])
      }
      if (chat.data) {
        setChatSession(chat.data)
        const msgs: ChatMessage[] = (chat.data.messages || []).map((m: any, idx: number) => ({
          id: `m${idx}`,
          role: (m.role as 'user' | 'assistant') ?? 'assistant',
          content: m.content,
          timestamp: m.timestamp ? Date.parse(m.timestamp) : Date.now(),
        }))
        setChatMessages(msgs)
      } else {
        setChatSession(null)
        setChatMessages([])
      }
    })()
  }, [selectedPlanId])

  // Actions
  const selectRepository = useCallback((id: string) => {
    setSelectedRepositoryId(id)
  }, [])

  const createRepository = useCallback(async (repo: { name: string; path: string; git_url?: string | null; default_branch?: string }) => {
    console.log('Creating repository:', repo)
    const res = await apiClient.createRepository(repo)
    console.log('Repository creation response:', res)
    if (res.data) {
      const r = res.data as any
      const newRepo: Repository = {
        id: r.id,
        name: r.name,
        path: r.path,
        gitUrl: r.git_url ?? null,
        defaultBranch: r.default_branch ?? 'main',
        createdAt: r.created_at,
        updatedAt: r.updated_at,
      }
      setRepositories(prev => [newRepo, ...prev])
      setSelectedRepositoryId(newRepo.id)
    } else if (res.error) {
      console.error('Repository creation error:', res.error)
      alert('Error creating repository: ' + res.error)
    }
  }, [])

  const deleteRepository = useCallback(async (id: string) => {
    await apiClient.deleteRepository(id)
    setRepositories(prev => prev.filter(r => r.id !== id))
    setSelectedRepositoryId(prev => (prev === id ? null : prev))
  }, [])

  const selectPlan = useCallback((id: string) => setSelectedPlanId(id), [])

  const createPlan = useCallback(async (payload: { name: string; description?: string; target_branch: string }) => {
    if (!selectedRepositoryId) return
    console.log('Creating plan:', payload, 'for repo:', selectedRepositoryId)
    const res = await apiClient.createPlan(selectedRepositoryId, payload)
    console.log('Plan creation response:', res)
    if (res.data) {
      const p = res.data as any
      const newPlan: Plan = {
        id: p.id,
        repositoryId: p.repository_id,
        name: p.name,
        description: p.description,
        targetBranch: p.target_branch,
        version: p.version,
        status: p.status,
        createdAt: p.created_at,
        updatedAt: p.updated_at,
      }
      setPlans(prev => [newPlan, ...prev])
      setSelectedPlanId(newPlan.id)
    } else if (res.error) {
      console.error('Plan creation error:', res.error)
      alert('Error creating plan: ' + res.error)
    }
  }, [selectedRepositoryId])

  const updatePlanName = useCallback((planId: string, newName: string) => {
    setPlans(prev => prev.map(plan =>
      plan.id === planId ? { ...plan, name: newName } : plan
    ))
  }, [])

  const deletePlan = useCallback(async (id: string) => {
    await apiClient.deletePlan(id)
    setPlans(prev => prev.filter(p => p.id !== id))
    setSelectedPlanId(prev => (prev === id ? null : prev))
  }, [])

  const sendMessage = useCallback(async (content: string) => {
    const trimmed = content.trim()
    if (!trimmed) return

    // optimistic update
    const userMsg: ChatMessage = { id: `m${Date.now()}`, role: 'user', content: trimmed, timestamp: Date.now() }
    setChatMessages(prev => [...prev, userMsg])

    // persist to backend chat session
    if (chatSession) {
      const updated = [...(chatSession.messages || []), { role: 'user', content: trimmed }]
      const res = await apiClient.updateChat(chatSession.id, { messages: updated })
      if (res.data) setChatSession(res.data)
    } else if (selectedPlanId) {
      const res = await apiClient.createPlanChat(selectedPlanId, { messages: [{ role: 'user', content: trimmed }] })
      if (res.data) setChatSession(res.data)
    }
  }, [chatSession, selectedPlanId])

  const generatePlan = useCallback(async (message: string) => {
    if (!selectedPlanId) return

    const trimmed = message.trim()
    if (!trimmed) return

    setIsLoading(true)

    // Add user message to chat
    const userMsg: ChatMessage = { id: `m${Date.now()}`, role: 'user', content: trimmed, timestamp: Date.now() }
    setChatMessages(prev => [...prev, userMsg])

    let assistantResponse = ''
    const assistantMsgId = `assistant-${Date.now()}`

    // Get current plan artifact content as string
    const currentPlanArtifact = artifacts.length > 0 
      ? artifacts.slice().sort((a, b) => (a.createdAt > b.createdAt ? -1 : 1))[0]
      : null
    
    let planArtifactString = ''
    if (currentPlanArtifact?.content) {
      const content = currentPlanArtifact.content
      // Extract text content from various possible structures
      if (typeof content === 'string') {
        planArtifactString = content
      } else if (content.text) {
        planArtifactString = content.text
      } else if (content.markdown) {
        planArtifactString = content.markdown
      } else if (content.plan) {
        planArtifactString = typeof content.plan === 'string' ? content.plan : JSON.stringify(content.plan, null, 2)
      } else if (content.content) {
        planArtifactString = typeof content.content === 'string' ? content.content : JSON.stringify(content.content, null, 2)
      } else {
        // Fallback to JSON string
        planArtifactString = JSON.stringify(content, null, 2)
      }
    }

    console.log('Sending plan generation request with:', {
      user_message: trimmed,
      plan_artifact_length: planArtifactString.length,
      plan_artifact_preview: planArtifactString.substring(0, 200) + (planArtifactString.length > 200 ? '...' : ''),
      chat_messages_count: chatMessages.length
    })

    // Start streaming plan generation
    const cleanup = apiClient.generatePlan(
      selectedPlanId,
      {
        user_message: trimmed,
        plan_artifact: planArtifactString, // Send as string
        chat_messages: chatMessages.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      },
      // onMessage callback
      (data) => {
        if (data.type === 'name_update') {
          // Update plan name dynamically
          updatePlanName(selectedPlanId, data.name)
        } else if (data.type === 'chunk') {
          assistantResponse += data.content
          // Update or add assistant message
          setChatMessages(prev => {
            const existingIndex = prev.findIndex(msg => msg.id === assistantMsgId)
            if (existingIndex >= 0) {
              const newMessages = [...prev]
              newMessages[existingIndex] = {
                ...newMessages[existingIndex],
                content: assistantResponse
              }
              return newMessages
            } else {
              return [...prev, {
                id: assistantMsgId,
                role: 'assistant' as const,
                content: assistantResponse,
                timestamp: Date.now()
              }]
            }
          })
        }
      },
      // onError callback
      (error) => {
        console.error('Plan generation error:', error)
        setChatMessages(prev => [...prev, {
          id: `error-${Date.now()}`,
          role: 'assistant' as const,
          content: 'Sorry, there was an error generating the plan. Please try again.',
          timestamp: Date.now()
        }])
        setIsLoading(false)
      },
      // onComplete callback
      () => {
        console.log('Plan generation completed')
        setIsLoading(false)
      }
    )

    // Store cleanup function if needed for component unmount
    // This could be expanded to handle multiple concurrent requests
  }, [selectedPlanId, chatMessages, updatePlanName])

  const value = useMemo<AppContextValue>(() => ({
    repositories,
    selectedRepositoryId,
    selectRepository,
    createRepository,
    deleteRepository,
    plans,
    selectedPlanId,
    selectPlan,
    createPlan,
    deletePlan,
    updatePlanName,
    chatMessages,
    sendMessage,
    generatePlan,
    isLoading,
    artifacts,
  }), [repositories, selectedRepositoryId, selectRepository, createRepository, deleteRepository, plans, selectedPlanId, selectPlan, createPlan, deletePlan, updatePlanName, chatMessages, sendMessage, generatePlan, isLoading, artifacts])

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useAppContext must be used within AppContextProvider')
  return ctx
}
