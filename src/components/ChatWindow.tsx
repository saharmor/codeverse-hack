'use client'

import React, { useMemo, useRef, useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, RefreshCw, Send, Mic } from 'lucide-react'
import { useAppContext } from '../lib/AppContext'
import VoiceRecorder from './VoiceRecorder'
import LoadingAnimation from './LoadingAnimation'
import { transcribeAudio } from '../lib/transcription'

function Avatar({ role }: { role: 'user' | 'assistant' }) {
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${role === 'assistant' ? 'bg-purple-600' : 'bg-gray-400'}`}>
      {role === 'assistant' ? 'AI' : 'U'}
    </div>
  )
}

export default function ChatWindow() {
  const { chatMessages, sendMessage, plans, selectedPlanId, isLoading } = useAppContext()
  const [input, setInput] = useState('')
  const [voiceBusy, setVoiceBusy] = useState(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const selectedPlan = useMemo(() => plans.find(p => p.id === selectedPlanId) || null, [plans, selectedPlanId])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [chatMessages])

  // Auto-resize textarea (starts at 1 row, grows as needed up to ~10 rows)
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const maxPx = 10 * 24
    el.style.height = Math.min(maxPx, el.scrollHeight) + 'px'
  }, [input])

  const handleSend = () => {
    if (!input.trim()) return
    sendMessage(input)
    setInput('')
  }



  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const onVoiceAccept = async (blob: Blob) => {
    setVoiceBusy(true)
    try {
      if (!selectedPlanId) throw new Error('No plan selected')
      const result = await transcribeAudio(selectedPlanId, blob)
      const text = result.corrected_text || result.raw_text || ''
      setInput(prev => {
        if (!prev) return text
        const spacer = prev.endsWith(' ') ? '' : ' '
        return prev + spacer + text
      })
    } catch (err: any) {
      console.error('Transcription failed:', err?.message || err)
      if (err?.details) console.error('Server details:', err.details)
      alert(`Transcription failed: ${err?.message || 'Unknown error'}`)
    } finally {
      setVoiceBusy(false)
    }
  }

  return (
    <section className="w-full h-full min-h-0 flex flex-col bg-white border-l border-gray-100" role="complementary">
      {/* Header */}
      <header className="shrink-0 border-b border-gray-100 px-4 py-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-900">{selectedPlan ? `${selectedPlan.name} – Chat` : 'Chat'}</h2>
        <div className="flex items-center gap-2">
          <button aria-label="Back" className="p-2 rounded-md hover:bg-gray-100 text-gray-600"><ChevronLeft className="w-4 h-4" /></button>
          <button aria-label="Forward" className="p-2 rounded-md hover:bg-gray-100 text-gray-600"><ChevronRight className="w-4 h-4" /></button>
          <button aria-label="Refresh" className="p-2 rounded-md hover:bg-gray-100 text-gray-600"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-6">
        {chatMessages.map(m => (
          <div key={m.id} className={`flex items-start gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
            {m.role === 'assistant' && <Avatar role="assistant" />}
            <div className={`max-w-[70%] rounded-2xl px-4 py-3 ${m.role === 'assistant' ? 'bg-gray-50 border border-gray-200 text-gray-900' : 'bg-purple-600 text-white'}`}>
              {m.content.split('\n').map((line, i) => (
                <p key={i} className="text-sm leading-relaxed whitespace-pre-wrap">{line}</p>
              ))}
            </div>
            {m.role === 'user' && <Avatar role="user" />}
          </div>
        ))}
        <LoadingAnimation isVisible={isLoading} />
      </div>

      {/* Footer */}
      <footer className="shrink-0 border-t border-gray-100 p-3">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <label htmlFor="composer" className="sr-only">Message</label>
            <div className="w-full rounded-2xl border border-gray-200 bg-white overflow-hidden">
              <textarea
                id="composer"
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Plan anything"
                rows={1}
                className="w-full resize-none max-h-40 px-4 py-2 text-sm leading-6 focus:outline-none"
              />
              <div className="px-2 py-1 flex items-center justify-between bg-white">
                <div className="flex-1 min-w-0">
                  <VoiceRecorder inline onAccept={onVoiceAccept} onCancel={() => {}} busy={voiceBusy} />
                </div>
                <div className="pl-3 flex items-center gap-2">
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || voiceBusy}
                    className="inline-flex items-center justify-center bg-purple-600 text-white w-10 h-10 rounded-full disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    aria-label="Send message"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
          {/* Right side controls column removed; send is in second row */}
        </div>
        <p className="mt-2 text-[11px] text-gray-500">
          Messages may be inaccurate. Verify important information.
        </p>
      </footer>
    </section>
  )
}
