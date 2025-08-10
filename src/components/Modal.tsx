"use client"

import React, { useEffect, useState } from "react"
import { createPortal } from "react-dom"

interface ModalProps {
  open: boolean
  title?: string
  onClose: () => void
  children: React.ReactNode
  footer?: React.ReactNode
}

export default function Modal({ open, title, onClose, children, footer }: ModalProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [open, onClose])

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [open])

  if (!open || !mounted) return null

  const content = (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
      onClick={onClose}
    >
      <div 
        role="dialog" 
        aria-modal="true"
        aria-labelledby={title ? "modal-title" : undefined}
        className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl border border-gray-200/80"
        style={{
          maxHeight: '90vh',
          margin: 'auto'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {title && (
          <div className="px-6 py-5 border-b border-gray-100 bg-gray-50/50 rounded-t-2xl">
            <div className="flex items-center justify-between">
              <h3 id="modal-title" className="text-lg font-semibold text-gray-900 leading-6">
                {title}
              </h3>
              <button
                onClick={onClose}
                className="rounded-lg p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
                aria-label="Close modal"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
        
        {/* Content */}
        <div className="px-6 py-6 max-h-[70vh] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
          <div className="space-y-4">
            {children}
          </div>
        </div>
        
        {/* Footer */}
        {footer && (
          <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/30 rounded-b-2xl">
            <div className="flex items-center justify-end gap-3">
              {footer}
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const target = document.getElementById('modal-root') || document.body
  return createPortal(content, target)
} 