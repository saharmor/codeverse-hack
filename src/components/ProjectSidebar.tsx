'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Folder, Plus, Trash2, FilePlus2, FileText } from 'lucide-react'
import { useAppContext } from '../lib/AppContext'
import Modal from './Modal'

export default function ProjectSidebar() {
  const {
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
  } = useAppContext()

  const containerRef = useRef<HTMLDivElement | null>(null)
  const [isWide, setIsWide] = useState(false)

  const [planModalOpen, setPlanModalOpen] = useState(false)
  const [planName, setPlanName] = useState('')



  // Auto-detect width to show names when expanded by resize handle
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width
        setIsWide(width >= 120)
      }
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  const handleAddRepository = useCallback(async () => {
    try {
      const { open } = await import('@tauri-apps/api/dialog')
      const res = await open({ 
        directory: true, 
        multiple: false,
        title: 'Select Repository Folder',
        defaultPath: '~/Documents'
      })
      if (typeof res === 'string') {
        // Extract folder name for repository name
        const folderName = res.split(/[\\/]/).filter(Boolean).pop() || 'Repository'
        await createRepository({ name: folderName, path: res, default_branch: 'main' })
      }
    } catch (error) {
      console.log('Running in web mode, folder picker not available')
      // Web fallback - show instruction
      alert('Folder picker is only available in the Tauri desktop app.')
    }
  }, [createRepository])

  const onSubmitPlan = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRepositoryId || !planName) return
    await createPlan({ name: planName, description: '', target_branch: 'main' })
    setPlanModalOpen(false)
    setPlanName('')
  }, [selectedRepositoryId, planName, createPlan])

  return (
    <aside ref={containerRef} className="w-full h-full bg-gray-50 border-r border-gray-100 flex flex-col py-3">
      <div className="px-3 flex items-center justify-between mb-2">
        {isWide && <span className="text-[10px] font-semibold text-purple-900 uppercase tracking-wide">Repositories</span>}
        {!isWide && <span className="text-[10px] font-semibold text-purple-900 uppercase tracking-wide">Repos</span>}
        <button onClick={handleAddRepository} aria-label="Add repository" className="p-1.5 rounded-md hover:bg-purple-100 text-purple-600 shrink-0 transition-colors">
          <Plus className="w-4 h-4 text-purple-600" />
        </button>
      </div>

      <nav className="flex-1 min-h-0 overflow-y-auto">
        <ul className="space-y-1 px-2">
          {repositories.map(repo => {
            const isActive = repo.id === selectedRepositoryId
            return (
              <li key={repo.id}>
                <div className={`group flex items-center gap-2 rounded-md px-2 py-1.5 cursor-pointer ${isActive ? 'bg-purple-100 text-purple-800' : 'text-gray-700 hover:bg-gray-100'}`} onClick={() => selectRepository(repo.id)} title={repo.path}>
                  <Folder className="w-4 h-4 shrink-0" />
                  {isWide && (
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium truncate">{repo.name}</div>
                      <div className="text-[10px] text-gray-500 truncate">{repo.path}</div>
                    </div>
                  )}
                  {isWide && (
                    <button onClick={(e) => { e.stopPropagation(); deleteRepository(repo.id) }} className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200 text-gray-700">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
                {isActive && (
                  <div className="mt-1 ml-6">
                    <div className="flex items-center justify-between pr-2">
                      <span className="text-[10px] uppercase tracking-wide text-gray-500">Plans</span>
                      <button onClick={() => setPlanModalOpen(true)} title="New plan" className="p-1 rounded hover:bg-purple-100 text-purple-600 transition-colors">
                        <FilePlus2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <ul className="mt-1 space-y-1">
                      {plans.map(plan => (
                        <li key={plan.id}>
                          <div className={`group flex items-center gap-2 rounded-md px-2 py-1.5 cursor-pointer ml-[-16px] pl-6 ${plan.id === selectedPlanId ? 'bg-purple-50 text-purple-800' : 'text-gray-700 hover:bg-gray-100'}`} onClick={() => selectPlan(plan.id)} title={plan.description || ''}>
                            <FileText className="w-3.5 h-3.5 shrink-0" />
                            {isWide && <div className="text-xs truncate flex-1">{plan.name}</div>}
                            {isWide && (
                              <button onClick={(e) => { e.stopPropagation(); deletePlan(plan.id) }} className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200 text-gray-700">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Create Plan Modal */}
      <Modal open={planModalOpen} title="New Plan" onClose={() => setPlanModalOpen(false)}
        footer={(
          <>
            <button 
              onClick={() => setPlanModalOpen(false)} 
              className="px-3 py-2 text-sm rounded-lg border border-gray-300 bg-white hover:bg-gray-50 text-gray-700"
            >
              Cancel
            </button>
            <button 
              onClick={(e) => { (document.getElementById('plan-form') as HTMLFormElement)?.requestSubmit() }} 
              className="px-3 py-2 text-sm rounded-lg bg-purple-600 hover:bg-purple-700 text-white"
            >
              Create
            </button>
          </>
        )}
      >
        <form id="plan-form" onSubmit={onSubmitPlan}>
          <input 
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-purple-500" 
            value={planName} 
            onChange={(e) => setPlanName(e.target.value)} 
            placeholder="Plan name"
            required 
            autoFocus
          />
        </form>
      </Modal>

    </aside>
  )
}
