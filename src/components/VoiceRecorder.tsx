'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Mic, Square, Check, X } from 'lucide-react'

interface VoiceRecorderProps {
  onAccept: (blob: Blob) => void
  onCancel?: () => void
  autoStart?: boolean
  inline?: boolean
}

export default function VoiceRecorder({ onAccept, onCancel, autoStart = false, inline = false }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [hasRecording, setHasRecording] = useState(false)
  const [permissionDenied, setPermissionDenied] = useState(false)
  const [level, setLevel] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const animationRef = useRef<number | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const reset = () => {
    setIsRecording(false)
    setHasRecording(false)
    setPermissionDenied(false)
    setLevel(0)
    chunksRef.current = []
  }

  const start = async () => {
    reset()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)()
      audioCtxRef.current = audioCtx

      const source = audioCtx.createMediaStreamSource(stream)
      sourceRef.current = source

      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 2048
      analyserRef.current = analyser
      source.connect(analyser)

      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }
      mediaRecorder.onstop = () => {
        setHasRecording(true)
        cancelAnimation()
        teardownStream()
      }

      mediaRecorder.start()
      setIsRecording(true)
      animateLevel()
    } catch (e) {
      setPermissionDenied(true)
    }
  }

  useEffect(() => {
    if (autoStart) {
      start()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const stop = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const accept = () => {
    if (!hasRecording) return
    const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
    onAccept(blob)
    reset()
  }

  const cancel = () => {
    if (isRecording) stop()
    reset()
    onCancel?.()
  }

  const animateLevel = () => {
    if (!analyserRef.current) return
    const analyser = analyserRef.current
    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const tick = () => {
      analyser.getByteTimeDomainData(dataArray)
      // Compute rough amplitude from time domain waveform
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const v = (dataArray[i] - 128) / 128
        sum += v * v
      }
      const rms = Math.sqrt(sum / dataArray.length)
      setLevel(rms)
      animationRef.current = requestAnimationFrame(tick)
    }
    animationRef.current = requestAnimationFrame(tick)
  }

  const cancelAnimation = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
  }

  const teardownStream = () => {
    if (sourceRef.current) {
      try { sourceRef.current.disconnect() } catch {}
      sourceRef.current = null
    }
    if (audioCtxRef.current) {
      try { audioCtxRef.current.close() } catch {}
      audioCtxRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    analyserRef.current = null
  }

  useEffect(() => {
    return () => {
      cancelAnimation()
      teardownStream()
    }
  }, [])

  // Simple bar waveform based on current "level"
  const bars = useMemo(() => {
    const count = inline ? 40 : 24
    const arr = Array.from({ length: count }, (_, i) => i)
    const intensity = Math.min(1, level * 4)
    return arr.map(i => {
      const phase = (i / count) * Math.PI * 2
      const h = 6 + Math.abs(Math.sin(phase)) * (inline ? 28 : 22) * (0.3 + intensity * 0.7)
      return Math.round(h)
    })
  }, [level, inline])

  if (inline) {
    return (
      <div className="w-full">
        <div className="w-full h-[52px] sm:h-[56px] rounded-2xl border border-gray-200 bg-gray-50 px-3 flex items-center justify-between overflow-hidden">
          <div className="flex items-end gap-[3px] h-[32px] sm:h-[36px] flex-1">
            {bars.map((h, i) => (
              <div key={i} style={{ height: `${h}px` }} className="w-[4px] bg-purple-500 rounded-sm" />
            ))}
          </div>
          <div className="flex items-center gap-2 pl-3">
            {isRecording ? (
              <button onClick={stop} aria-label="Stop recording" className="p-2 rounded-md bg-red-50 hover:bg-red-100 text-red-600">
                <Square className="w-4 h-4" />
              </button>
            ) : (
              <>
                <button onClick={accept} aria-label="Accept transcription" className="p-2 rounded-md bg-green-50 hover:bg-green-100 text-green-700">
                  <Check className="w-4 h-4" />
                </button>
                <button onClick={cancel} aria-label="Discard" className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700">
                  <X className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>
        {permissionDenied && (
          <p className="mt-2 text-xs text-red-600">Microphone permission denied. Enable it in System Settings &gt; Privacy &amp; Security &gt; Microphone.</p>
        )}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      {!isRecording && !hasRecording && (
        <button onClick={start} aria-label="Start voice" className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700">
          <Mic className="w-4 h-4" />
        </button>
      )}

      {isRecording && (
        <button onClick={stop} aria-label="Stop recording" className="p-2 rounded-md bg-red-50 hover:bg-red-100 text-red-600">
          <Square className="w-4 h-4" />
        </button>
      )}

      {(isRecording || hasRecording) && (
        <div className="flex-1 min-w-[140px] max-w-[280px] h-10 bg-gray-50 border border-gray-200 rounded-lg px-3 flex items-center overflow-hidden">
          <div className="flex items-end gap-[3px] h-full w-full">
            {bars.map((h, i) => (
              <div key={i} style={{ height: `${h}px` }} className="w-[4px] bg-purple-500 rounded-sm" />
            ))}
          </div>
        </div>
      )}

      {hasRecording && !isRecording && (
        <>
          <button onClick={accept} aria-label="Accept transcription" className="p-2 rounded-md bg-green-50 hover:bg-green-100 text-green-700">
            <Check className="w-4 h-4" />
          </button>
          <button onClick={cancel} aria-label="Discard" className="p-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-700">
            <X className="w-4 h-4" />
          </button>
        </>
      )}

      {permissionDenied && (
        <span className="text-xs text-red-600">Microphone permission denied</span>
      )}
    </div>
  )
} 