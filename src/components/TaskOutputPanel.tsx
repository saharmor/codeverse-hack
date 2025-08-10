'use client'

import React from 'react'
import { Download, X } from 'lucide-react'

export default function TaskOutputPanel() {
  return (
    <aside className="w-full h-full border-l border-gray-100 bg-white flex flex-col">
      <header className="shrink-0 px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">Task Output</h3>
        <div className="flex items-center gap-1">
          <button aria-label="Download" className="p-2 rounded-md hover:bg-gray-100 text-gray-600"><Download className="w-4 h-4" /></button>
          <button aria-label="Close" className="p-2 rounded-md hover:bg-gray-100 text-gray-600"><X className="w-4 h-4" /></button>
        </div>
      </header>
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        <section>
          <h4 className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Executive Summary</h4>
          <p className="mt-1 text-sm text-gray-700">This session will design a Claude-like tri-pane UI with responsive panels, scroll management, and accessible controls.</p>
        </section>

        <section>
          <h4 className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Important Notes</h4>
          <pre className="mt-2 text-xs bg-gray-50 border border-gray-200 rounded-lg p-3 overflow-x-auto"><code>{`- Left sidebar is fixed at 56px
- Right panel is fixed at 272px
- Center pane is flexible and scrolls independently
- Use Tailwind for styling and transitions`}</code></pre>
        </section>

        <section>
          <h4 className="text-xs font-semibold text-purple-700 uppercase tracking-wide">System Architecture</h4>
          <p className="mt-1 text-sm text-gray-700">UI built with Next.js (React + TypeScript), styled by Tailwind, hosted in Tauri. State shared via React context.</p>
        </section>

        <section>
          <h4 className="text-xs font-semibold text-purple-700 uppercase tracking-wide">Implementation Timeline</h4>
          <ul className="mt-2 space-y-2 text-sm text-gray-700">
            <li className="flex items-center gap-2"><input type="checkbox" checked readOnly className="accent-purple-600" /> Layout skeleton</li>
            <li className="flex items-center gap-2"><input type="checkbox" checked readOnly className="accent-purple-600" /> Panel components</li>
            <li className="flex items-center gap-2"><input type="checkbox" checked readOnly className="accent-purple-600" /> State & interactions</li>
            <li className="flex items-center gap-2"><input type="checkbox" readOnly className="accent-purple-600" /> Polish & accessibility</li>
          </ul>
        </section>
      </div>
    </aside>
  )
} 