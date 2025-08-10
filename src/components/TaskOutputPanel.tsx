'use client'

import React, { useMemo, useState } from 'react'
import { useAppContext } from '../lib/AppContext'

function ArtifactViewer({ artifact }: { artifact: any }) {
  const type = artifact.artifactType || artifact.artifact_type
  const content = artifact.content || {}

  if (type === 'feature_plan' && (content.text || content.markdown)) {
    return (
      <article className="prose prose-sm max-w-none">
        <pre className="whitespace-pre-wrap text-sm">{content.text || content.markdown}</pre>
      </article>
    )
  }

  if (type === 'implementation_steps' && Array.isArray(content.steps)) {
    return (
      <ol className="list-decimal pl-5 space-y-1 text-sm">
        {content.steps.map((s: any, i: number) => (
          <li key={i}>{typeof s === 'string' ? s : JSON.stringify(s, null, 2)}</li>
        ))}
      </ol>
    )
  }

  if (type === 'code_changes' && content.diff) {
    return (
      <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-auto text-xs">
        <code>{content.diff}</code>
      </pre>
    )
  }

  return (
    <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-auto text-xs">
      <code>{JSON.stringify(content, null, 2)}</code>
    </pre>
  )
}

export default function TaskOutputPanel() {
  const { artifacts, plans, selectedPlanId } = useAppContext()
  const [activeId, setActiveId] = useState<string | null>(null)

  const selectedPlan = useMemo(() => plans.find(p => p.id === selectedPlanId) || null, [plans, selectedPlanId])

  const ordered = useMemo(() => artifacts.slice().sort((a, b) => (a.createdAt > b.createdAt ? -1 : 1)), [artifacts])
  const active = useMemo(() => ordered.find(a => a.id === (activeId || ordered[0]?.id)) || null, [ordered, activeId])

  return (
    <main className="w-full h-full bg-white flex flex-col">
      <header className="shrink-0 px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">{selectedPlan ? selectedPlan.name : 'Task Output'}</h3>
      </header>

      <div className="flex-1 min-h-0 flex">
        <aside className="w-56 shrink-0 border-r border-gray-100 p-3 overflow-y-auto">
          <ul className="space-y-1">
            {ordered.map(a => (
              <li key={a.id}>
                <button onClick={() => setActiveId(a.id)} className={`w-full text-left rounded-md px-2 py-1.5 text-sm ${a.id === active?.id ? 'bg-purple-50 text-purple-800' : 'hover:bg-gray-100 text-gray-800'}`}>
                  <div className="font-medium truncate">{String((a as any).artifactType ?? (a as any).artifact_type).replace(/_/g, ' ')}</div>
                  <div className="text-[10px] text-gray-500 truncate">{new Date((a as any).createdAt ?? (a as any).created_at).toLocaleString()}</div>
                </button>
              </li>
            ))}
            {ordered.length === 0 && (
              <li className="text-xs text-gray-500">No artifacts yet.</li>
            )}
          </ul>
        </aside>
        <section className="flex-1 min-w-0 min-h-0 p-4 overflow-y-auto">
          {active ? <ArtifactViewer artifact={active} /> : (
            <div className="text-sm text-gray-500">Select a plan to view artifacts.</div>
          )}
        </section>
      </div>
    </main>
  )
}
