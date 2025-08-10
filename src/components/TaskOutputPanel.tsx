'use client'

import React from 'react'
import MarkdownEditor from './MarkdownEditor'

export default function TaskOutputPanel() {
  return (
    <main className="w-full h-full bg-white flex flex-col">
      <div className="flex-1 min-h-0">
        <MarkdownEditor 
          placeholder="Start writing your plan or notes in markdown..."
        />
      </div>
    </main>
  )
}
