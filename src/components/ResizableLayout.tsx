'use client'

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ProjectSidebar from './ProjectSidebar'
import ChatWindow from './ChatWindow'
import TaskOutputPanel from './TaskOutputPanel'

const MIN_LEFT = 48
const MAX_LEFT = 320
const MIN_RIGHT = 200
const MAX_RIGHT = 520

export default function ResizableLayout() {
  const [leftWidth, setLeftWidth] = useState<number>(56)
  const [rightWidth, setRightWidth] = useState<number>(272)
  const [dragging, setDragging] = useState<'left' | 'right' | null>(null)
  const startXRef = useRef<number>(0)
  const startLeftRef = useRef<number>(leftWidth)
  const startRightRef = useRef<number>(rightWidth)

  const [windowWidth, setWindowWidth] = useState<number>(typeof window !== 'undefined' ? window.innerWidth : 1200)

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const showRightPanel = windowWidth >= 900

  const onMouseDownLeft = (e: React.MouseEvent) => {
    setDragging('left')
    startXRef.current = e.clientX
    startLeftRef.current = leftWidth
  }

  const onMouseDownRight = (e: React.MouseEvent) => {
    setDragging('right')
    startXRef.current = e.clientX
    startRightRef.current = rightWidth
  }

  const onKeyResizeLeft = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault()
      const delta = e.key === 'ArrowRight' ? 8 : -8
      setLeftWidth(prev => Math.min(MAX_LEFT, Math.max(MIN_LEFT, prev + delta)))
    }
  }

  const onKeyResizeRight = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault()
      const delta = e.key === 'ArrowLeft' ? 8 : -8
      setRightWidth(prev => Math.min(MAX_RIGHT, Math.max(MIN_RIGHT, prev + delta)))
    }
  }

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging) return
      if (dragging === 'left') {
        const delta = e.clientX - startXRef.current
        const next = Math.min(MAX_LEFT, Math.max(MIN_LEFT, startLeftRef.current + delta))
        setLeftWidth(next)
      } else if (dragging === 'right') {
        const delta = startXRef.current - e.clientX
        const next = Math.min(MAX_RIGHT, Math.max(MIN_RIGHT, startRightRef.current + delta))
        setRightWidth(next)
      }
    }

    const onMouseUp = () => {
      setDragging(null)
    }

    if (dragging) {
      window.addEventListener('mousemove', onMouseMove)
      window.addEventListener('mouseup', onMouseUp, { once: true })
      document.body.classList.add('select-none', 'cursor-col-resize')
    }

    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
      document.body.classList.remove('select-none', 'cursor-col-resize')
    }
  }, [dragging])

  // Wider hotzone with visible center grip for better discoverability
  const handleContainerClass = 'group relative z-20 w-3 md:w-3.5 h-full touch-none cursor-col-resize hover:bg-gray-100/40 transition-colors'
  const handleGrip = (
    <span
      className="pointer-events-none absolute inset-y-0 left-1/2 -translate-x-1/2 w-px bg-gray-200 group-hover:w-1.5 group-hover:bg-gray-300 rounded"
      aria-hidden
    />
  )

  return (
    <div className={`h-screen w-screen flex overflow-hidden ${dragging ? 'cursor-col-resize select-none' : ''}`}>
      <div style={{ width: leftWidth }} className="shrink-0 h-full">
        <ProjectSidebar />
      </div>
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize project sidebar"
        title="Drag to resize"
        tabIndex={0}
        className={handleContainerClass}
        style={{ cursor: 'col-resize' }}
        onMouseDown={onMouseDownLeft}
        onKeyDown={onKeyResizeLeft}
      >
        {handleGrip}
      </div>
      <div className="flex-1 min-w-0 min-h-0 h-full flex">
        <TaskOutputPanel />
      </div>
      {showRightPanel && (
        <>
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize chat panel"
            title="Drag to resize"
            tabIndex={0}
            className={handleContainerClass}
            style={{ cursor: 'col-resize' }}
            onMouseDown={onMouseDownRight}
            onKeyDown={onKeyResizeRight}
          >
            {handleGrip}
          </div>
          <div style={{ width: rightWidth }} className="shrink-0 h-full flex min-h-0 items-stretch">
            <ChatWindow />
          </div>
        </>
      )}
    </div>
  )
}
