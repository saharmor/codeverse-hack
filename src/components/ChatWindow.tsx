'use client'

import React, { useMemo, useRef, useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, RefreshCw, Send, Mic } from 'lucide-react'
import { useAppContext } from '../lib/AppContext'
import VoiceRecorder from './VoiceRecorder'
import { transcribeAudioDummy } from '../lib/transcription'

function Avatar({ role }: { role: 'user' | 'assistant' }) {
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${role === 'assistant' ? 'bg-purple-600' : 'bg-gray-400'}`}>
      {role === 'assistant' ? 'AI' : 'U'}
    </div>
  )
}

export default function ChatWindow() {
  const { chatMessages, sendMessage } = useAppContext()
  const [input, setInput] = useState('')
  const [queued, setQueued] = useState<string | null>(null)
  const [voiceBusy, setVoiceBusy] = useState(false)
  const [inlineRecording, setInlineRecording] = useState(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  const suggestions = useMemo(() => [
    'What are the key tasks to start with?',
    'Generate a high-level architecture plan',
    'List risks and open questions',
  ], [])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [chatMessages])

  const handleSend = () => {
    if (!input.trim()) return
    sendMessage(input)
    setInput('')
    setQueued(null)
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
      const text = await transcribeAudioDummy(blob)
      setInput(text)
      setInlineRecording(false)
    } finally {
      setVoiceBusy(false)
    }
  }

  return (
    <section className="flex-1 min-w-0 h-full flex flex-col bg-white" role="main">
      {/* Header */}
      <header className="shrink-0 border-b border-gray-100 px-4 py-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-900">Hello There - Canvas</h2>
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

        {/* Clarifying questions */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => { setQueued(s); setInput(s) }}
              className={`text-left rounded-xl border border-gray-200 bg-gray-50 hover:bg-gray-100 transition-colors px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500`}
              aria-label={`Use suggestion: ${s}`}
            >
              <p className="text-xs text-gray-700">{s}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="shrink-0 border-t border-gray-100 p-3">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <label htmlFor="composer" className="sr-only">Message</label>
            {inlineRecording ? (
              <VoiceRecorder inline autoStart onAccept={onVoiceAccept} onCancel={() => setInlineRecording(false)} />
            ) : (
              <textarea
                id="composer"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Message Claude..."
                className="w-full resize-none max-h-40 min-h-[44px] rounded-2xl border border-gray-200 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            )}
          </div>
          <div className="flex flex-col items-stretch gap-2">
            {!inlineRecording && (
              <button
                onClick={() => setInlineRecording(true)}
                disabled={voiceBusy}
                className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700"
                aria-label="Start voice"
              >
                <Mic className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={handleSend}
              disabled={!input.trim() || voiceBusy || inlineRecording}
              className="inline-flex items-center justify-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-xl disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-purple-500"
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
              <span className="text-sm">Send</span>
            </button>
          </div>
        </div>
        <p className="mt-2 text-[11px] text-gray-500">
          Messages may be inaccurate. Verify important information.
        </p>
      </footer>
    </section>
  )
}
