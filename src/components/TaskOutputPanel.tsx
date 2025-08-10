'use client'

import React, { useMemo } from 'react'
import { useAppContext } from '../lib/AppContext'
import MarkdownEditor from './MarkdownEditor'

function ArtifactViewer({ artifact, onContentChange }: { artifact: any, onContentChange?: (content: string) => void }) {
  const type = artifact.artifactType || artifact.artifact_type
  const content = artifact.content || {}

  // Handle plan_version type (from PlanVersion model)
  if (type === 'plan_version') {
    // Try to extract text content from various possible structures
    let textContent = ''
    
    if (typeof content === 'string') {
      textContent = content
    } else if (content.text) {
      textContent = content.text
    } else if (content.markdown) {
      textContent = content.markdown
    } else if (content.plan) {
      textContent = typeof content.plan === 'string' ? content.plan : JSON.stringify(content.plan, null, 2)
    } else if (content.content) {
      textContent = typeof content.content === 'string' ? content.content : JSON.stringify(content.content, null, 2)
    } else {
      // Fallback to showing the whole content as JSON
      textContent = JSON.stringify(content, null, 2)
    }

    return (
      <div className="space-y-4 h-full flex flex-col">
        {artifact.version && (
          <div className="text-xs text-gray-500 bg-gray-50 px-3 py-1 rounded-md inline-block">
            Version {artifact.version}
          </div>
        )}
        <div className="flex-1 min-h-0">
          <MarkdownEditor 
            value={textContent}
            onChange={onContentChange}
            placeholder="Plan content will appear here..."
            className="h-full"
          />
        </div>
      </div>
    )
  }

  if (type === 'feature_plan' && (content.text || content.markdown)) {
    return (
      <div className="h-full">
        <MarkdownEditor 
          value={content.text || content.markdown}
          onChange={onContentChange}
          placeholder="Feature plan content will appear here..."
          className="h-full"
        />
      </div>
    )
  }

  if (type === 'implementation_steps' && Array.isArray(content.steps)) {
    // Convert steps array to markdown format
    const markdownSteps = content.steps.map((s: any, i: number) => {
      const stepText = typeof s === 'string' ? s : JSON.stringify(s, null, 2)
      return `${i + 1}. ${stepText}`
    }).join('\n\n')
    
    return (
      <div className="h-full">
        <MarkdownEditor 
          value={markdownSteps}
          onChange={onContentChange}
          placeholder="Implementation steps will appear here..."
          className="h-full"
        />
      </div>
    )
  }

  if (type === 'code_changes' && content.diff) {
    // Wrap diff in markdown code block for better formatting
    const diffMarkdown = '```diff\n' + content.diff + '\n```'
    
    return (
      <div className="h-full">
        <MarkdownEditor 
          value={diffMarkdown}
          onChange={onContentChange}
          placeholder="Code changes will appear here..."
          className="h-full"
        />
      </div>
    )
  }

  // Fallback for other content types - display as formatted JSON in markdown
  const jsonMarkdown = '```json\n' + JSON.stringify(content, null, 2) + '\n```'
  
  return (
    <div className="space-y-4 h-full flex flex-col">
      {artifact.version && (
        <div className="text-xs text-gray-500 bg-gray-50 px-3 py-1 rounded-md inline-block">
          Version {artifact.version}
        </div>
      )}
      <div className="flex-1 min-h-0">
        <MarkdownEditor 
          value={jsonMarkdown}
          onChange={onContentChange}
          placeholder="Artifact content will appear here..."
          className="h-full"
        />
      </div>
    </div>
  )
}

export default function TaskOutputPanel() {
  const { artifacts, plans, selectedPlanId, updateArtifact } = useAppContext()

  const selectedPlan = useMemo(() => plans.find(p => p.id === selectedPlanId) || null, [plans, selectedPlanId])

  // Always get the latest artifact (most recent by creation date)
  const latestArtifact = useMemo(() => {
    if (artifacts.length === 0) return null
    return artifacts.slice().sort((a, b) => (a.createdAt > b.createdAt ? -1 : 1))[0]
  }, [artifacts])

  return (
    <main className="w-full h-full bg-white flex flex-col">
      <header className="shrink-0 px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">{selectedPlan ? selectedPlan.name : 'Task Output'}</h3>
      </header>

      <div className="flex-1 min-h-0 flex">
        {/* Only show sidebar if no plan is selected AND there are artifacts */}
        {!selectedPlanId && artifacts.length > 0 && (
          <aside className="w-56 shrink-0 border-r border-gray-100 p-3 overflow-y-auto">
            <ul className="space-y-1">
              {artifacts.map(a => (
                <li key={a.id}>
                  <div className="w-full text-left rounded-md px-2 py-1.5 text-sm text-gray-800">
                    <div className="font-medium truncate">
                      {String((a as any).artifactType ?? (a as any).artifact_type).replace(/_/g, ' ')}
                      {(a as any).version && (
                        <span className="ml-1 text-xs text-gray-500">v{(a as any).version}</span>
                      )}
                    </div>
                    <div className="text-[10px] text-gray-500 truncate">{new Date((a as any).createdAt ?? (a as any).created_at).toLocaleString()}</div>
                  </div>
                </li>
              ))}
            </ul>
          </aside>
        )}
        
        <section className={`min-w-0 min-h-0 p-4 overflow-y-auto ${!selectedPlanId && artifacts.length > 0 ? 'flex-1' : 'w-full'}`}>
          {latestArtifact ? (
            <ArtifactViewer 
              artifact={latestArtifact} 
              onContentChange={(content: string) => updateArtifact(latestArtifact.id, content)}
            />
          ) : (
            <div className="text-sm text-gray-500">
              {selectedPlanId ? 'No artifacts available for this plan.' : 'Select a plan to view artifacts.'}
            </div>
          )}
        </section>
      </div>
    </main>
  )
}
