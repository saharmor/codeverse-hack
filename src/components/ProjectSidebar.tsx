'use client'

import React from 'react'
import { Folder, LayoutDashboard, Plus } from 'lucide-react'
import { useAppContext } from '../lib/AppContext'

export default function ProjectSidebar() {
  const { projects, selectedProjectId, selectProject, addProject } = useAppContext()

  return (
    <aside className="w-full h-full bg-gray-50 border-r border-gray-100 flex flex-col items-center py-3 gap-3">
      <div className="shrink-0">
        <span className="text-[10px] font-semibold text-purple-900">Projects</span>
      </div>
      <nav className="flex-1 min-h-0 overflow-y-auto w-full flex flex-col items-center gap-2">
        {projects.map(project => {
          const isActive = project.id === selectedProjectId
          const Icon = project.icon === 'dashboard' ? LayoutDashboard : Folder
          return (
            <button
              key={project.id}
              onClick={() => selectProject(project.id)}
              title={`${project.name}${project.path ? `\n${project.path}` : ''}${project.lastUpdated ? `\nUpdated ${project.lastUpdated}` : ''}`}
              aria-label={`Select project ${project.name}`}
              className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                isActive ? 'bg-purple-100 text-purple-700 ring-1 ring-purple-200' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-5 h-5" />
            </button>
          )
        })}
      </nav>
      <div className="shrink-0">
        <button
          onClick={() => addProject({ name: 'New Repository', icon: 'folder', path: '~/projects/new', lastUpdated: new Date().toISOString().slice(0, 10) })}
          aria-label="Add repository"
          title="Add repository"
          className="w-10 h-10 rounded-lg flex items-center justify-center text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>
    </aside>
  )
} 