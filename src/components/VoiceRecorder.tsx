import React, { useEffect, useRef, useState } from 'react'
import { Mic, Check, X } from 'lucide-react'

interface VoiceRecorderProps {
  onAccept: (blob: Blob) => void
  onCancel?: () => void
  autoStart?: boolean
  inline?: boolean
}

export default function VoiceRecorder({
  onAccept,
  onCancel,
  autoStart = false,
  inline = false
}: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [hasRecording, setHasRecording] = useState(false)
  const [permissionDenied, setPermissionDenied] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [bars, setBars] = useState<number[]>([])

  const mediaRecorderRef = useRef<MediaRecorder | null>(null) // unused in WAV path, kept for reference
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const silentGainRef = useRef<GainNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const floatChunksRef = useRef<Float32Array[]>([])

  // Initialize bars array
  useEffect(() => {
    const barCount = inline ? 40 : 24
    setBars(new Array(barCount).fill(8))
  }, [inline])

  const startAudioAnalysis = () => {
    if (!analyserRef.current) return

    const analyser = analyserRef.current
    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    const timeDataArray = new Uint8Array(analyser.fftSize)

    const updateBars = () => {
      if (!analyserRef.current || !isRecording) return

      // Get both frequency and time domain data
      analyser.getByteFrequencyData(dataArray)
      analyser.getByteTimeDomainData(timeDataArray)

      // Calculate RMS (Root Mean Square) for better audio level detection
      let rms = 0
      for (let i = 0; i < timeDataArray.length; i++) {
        const normalized = (timeDataArray[i] - 128) / 128
        rms += normalized * normalized
      }
      rms = Math.sqrt(rms / timeDataArray.length)
      setAudioLevel(rms)

      // Generate bar heights
      const barCount = inline ? 40 : 24
      const newBars: number[] = []

      // Use more frequency data for better visualization
      const usableRange = Math.min(bufferLength / 2, 128)

      for (let i = 0; i < barCount; i++) {
        // Better frequency mapping
        const freqIndex = Math.floor((i / barCount) * usableRange)
        const nextFreqIndex = Math.floor(((i + 1) / barCount) * usableRange)

        // Average frequency data in this range
        let sum = 0
        let count = 0
        for (let j = freqIndex; j < nextFreqIndex && j < dataArray.length; j++) {
          sum += dataArray[j]
          count++
        }

        const average = count > 0 ? sum / count : 0
        let normalizedValue = average / 255

        // Apply sensitivity boost for quiet audio
        normalizedValue = Math.pow(normalizedValue, 0.6)

        // Add some baseline activity when there's any audio
        if (rms > 0.01) {
          normalizedValue = Math.max(normalizedValue, 0.1 + (rms * 0.3))
        }

        // Add subtle randomness for natural movement
        const randomness = 0.05 * Math.random()
        normalizedValue = Math.min(1, normalizedValue + randomness)

        // Convert to pixel height
        const minHeight = 6
        const maxHeight = inline ? 36 : 32
        const height = Math.round(minHeight + (normalizedValue * (maxHeight - minHeight)))

        newBars.push(height)
      }

      setBars(newBars)
      animationFrameRef.current = requestAnimationFrame(updateBars)
    }

    // Start the animation loop
    animationFrameRef.current = requestAnimationFrame(updateBars)
  }

  const stopAudioAnalysis = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
  }

  const startRecording = async () => {
    try {
      console.log('Starting recording...')

      // Reset state
      setPermissionDenied(false)
      chunksRef.current = []
      floatChunksRef.current = []

      // Get microphone access with better constraints
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      })
      streamRef.current = stream

      // Create audio context and analyser
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext
      const audioContext = new AudioContext()
      audioContextRef.current = audioContext

      // Resume audio context if suspended
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }

      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256 // Smaller for better performance
      analyser.smoothingTimeConstant = 0.9 // More smoothing
      analyser.minDecibels = -100
      analyser.maxDecibels = -30
      analyserRef.current = analyser

      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)

      // Create ScriptProcessorNode to capture PCM for WAV encoding
      const processor = audioContext.createScriptProcessor(4096, 1, 1)
      processorRef.current = processor
      source.connect(processor)

      // Route processor to a silent gain to keep the node active without audible output
      const silentGain = audioContext.createGain()
      silentGain.gain.value = 0
      silentGainRef.current = silentGain
      processor.connect(silentGain)
      silentGain.connect(audioContext.destination)

      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0)
        // Copy the Float32Array as the buffer is reused each tick
        floatChunksRef.current.push(new Float32Array(input))
      }

      setIsRecording(true)

      // Start audio visualization
      startAudioAnalysis()

      console.log('Recording started successfully')

    } catch (error) {
      console.error('Failed to start recording:', error)
      setPermissionDenied(true)
      setIsRecording(false)
    }
  }

  const stopRecording = () => {
    console.log('Stopping recording...')
    // Stop WAV capture
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current.onaudioprocess = null
      processorRef.current = null
    }
    if (silentGainRef.current) {
      try { silentGainRef.current.disconnect() } catch {}
      silentGainRef.current = null
    }
    setHasRecording(floatChunksRef.current.length > 0)
    setIsRecording(false)
    stopAudioAnalysis()
  }

  function encodeWavFromFloat32(chunks: Float32Array[], sampleRate: number): Blob {
    // Concatenate Float32 chunks
    const length = chunks.reduce((sum, c) => sum + c.length, 0)
    const buffer = new Float32Array(length)
    let offset = 0
    for (const c of chunks) {
      buffer.set(c, offset)
      offset += c.length
    }

    // Convert to 16-bit PCM
    const pcmBuffer = new Int16Array(buffer.length)
    for (let i = 0; i < buffer.length; i++) {
      const s = Math.max(-1, Math.min(1, buffer[i]))
      pcmBuffer[i] = s < 0 ? s * 0x8000 : s * 0x7fff
    }

    const bytesPerSample = 2 // 16-bit
    const numChannels = 1
    const blockAlign = numChannels * bytesPerSample
    const byteRate = sampleRate * blockAlign
    const dataSize = pcmBuffer.length * bytesPerSample
    const bufferSize = 44 + dataSize
    const arrayBuffer = new ArrayBuffer(bufferSize)
    const view = new DataView(arrayBuffer)

    // RIFF header
    function writeString(offset: number, str: string) {
      for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
    }
    let pos = 0
    writeString(pos, 'RIFF'); pos += 4
    view.setUint32(pos, 36 + dataSize, true); pos += 4
    writeString(pos, 'WAVE'); pos += 4
    // fmt chunk
    writeString(pos, 'fmt '); pos += 4
    view.setUint32(pos, 16, true); pos += 4 // PCM chunk size
    view.setUint16(pos, 1, true); pos += 2  // PCM format
    view.setUint16(pos, numChannels, true); pos += 2
    view.setUint32(pos, sampleRate, true); pos += 4
    view.setUint32(pos, byteRate, true); pos += 4
    view.setUint16(pos, blockAlign, true); pos += 2
    view.setUint16(pos, bytesPerSample * 8, true); pos += 2 // bits per sample
    // data chunk
    writeString(pos, 'data'); pos += 4
    view.setUint32(pos, dataSize, true); pos += 4

    // PCM data
    let dataPos = pos
    for (let i = 0; i < pcmBuffer.length; i++, dataPos += 2) {
      view.setInt16(dataPos, pcmBuffer[i], true)
    }

    return new Blob([view], { type: 'audio/wav' })
  }

  const acceptRecording = () => {
    if (isRecording) {
      stopRecording()
      // Wait a bit for the stop event to process
      setTimeout(() => {
        if (floatChunksRef.current.length > 0 && audioContextRef.current) {
          const wavBlob = encodeWavFromFloat32(floatChunksRef.current, audioContextRef.current.sampleRate)
          onAccept(wavBlob)
          reset()
        }
      }, 100)
    } else if (hasRecording) {
      if (floatChunksRef.current.length > 0 && audioContextRef.current) {
        const wavBlob = encodeWavFromFloat32(floatChunksRef.current, audioContextRef.current.sampleRate)
        onAccept(wavBlob)
        reset()
      }
    }
  }

  const cancelRecording = () => {
    console.log('Cancelling recording...')
    if (isRecording) {
      stopRecording()
    }
    reset()
    onCancel?.()
  }

  const reset = () => {
    console.log('Resetting recorder...')
    setIsRecording(false)
    setHasRecording(false)
    setPermissionDenied(false)
    setAudioLevel(0)

    const barCount = inline ? 40 : 24
    setBars(new Array(barCount).fill(8))
    chunksRef.current = []
    floatChunksRef.current = []

    stopAudioAnalysis()

    // Clean up media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop()
        console.log('Stopped track:', track.kind)
      })
      streamRef.current = null
    }

    // Clean up audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    if (processorRef.current) {
      try { processorRef.current.disconnect() } catch {}
      processorRef.current.onaudioprocess = null
      processorRef.current = null
    }
    if (silentGainRef.current) {
      try { silentGainRef.current.disconnect() } catch {}
      silentGainRef.current = null
    }

    analyserRef.current = null
    mediaRecorderRef.current = null
  }

  // Auto-start if requested
  useEffect(() => {
    if (autoStart) {
      startRecording()
    }

    return () => {
      reset()
    }
  }, [autoStart])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      reset()
    }
  }, [])

  if (inline) {
    return (
      <div className="w-full max-w-md mx-auto p-4">
        <div className="w-full h-[56px] rounded-2xl border-2 border-gray-200 bg-white px-4 flex items-center justify-between overflow-hidden shadow-sm">
          {/* Waveform bars */}
          <div className="flex items-end gap-[1.5px] h-[36px] flex-1">
            {bars.map((height, index) => (
              <div
                key={index}
                className={`w-[2.5px] rounded-sm transition-all duration-75 ${
                  isRecording
                    ? 'bg-gradient-to-t from-purple-600 to-purple-400'
                    : hasRecording
                      ? 'bg-gradient-to-t from-green-600 to-green-400'
                      : 'bg-gray-300'
                }`}
                style={{
                  height: `${height}px`,
                  opacity: isRecording ? 0.7 + (audioLevel * 0.3) : 0.6
                }}
              />
            ))}
          </div>

          {/* Control buttons */}
          <div className="flex items-center gap-2 pl-3">
            {!isRecording && !hasRecording && (
              <button
                onClick={startRecording}
                className="p-2 rounded-full bg-blue-50 hover:bg-blue-100 text-blue-700 transition-colors"
                aria-label="Start recording"
              >
                <Mic className="w-4 h-4" />
              </button>
            )}

            {(isRecording || hasRecording) && (
              <>
                <button
                  onClick={acceptRecording}
                  className="p-2 rounded-full bg-green-50 hover:bg-green-100 text-green-700 transition-colors"
                  aria-label="Accept recording"
                >
                  <Check className="w-4 h-4" />
                </button>
                <button
                  onClick={cancelRecording}
                  className="p-2 rounded-full bg-red-50 hover:bg-red-100 text-red-700 transition-colors"
                  aria-label="Cancel recording"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Status indicator */}
        <div className="mt-3 text-center">
          {isRecording && (
            <div className="flex items-center justify-center gap-2 text-sm text-purple-600">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              Recording... (Level: {(audioLevel * 100).toFixed(1)}%)
            </div>
          )}
          {hasRecording && !isRecording && (
            <div className="text-sm text-green-600">
              Recording complete - accept or cancel
            </div>
          )}
          {!isRecording && !hasRecording && (
            <div className="text-sm text-gray-500">
              Click microphone to start recording
            </div>
          )}
        </div>

        {permissionDenied && (
          <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">
              Microphone access denied. Please enable microphone permissions in your browser settings and refresh the page.
            </p>
          </div>
        )}
      </div>
    )
  }

  // Non-inline version
  return (
    <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
      {/* Start button */}
      {!isRecording && !hasRecording && (
        <button
          onClick={startRecording}
          className="p-3 rounded-full bg-blue-500 hover:bg-blue-600 text-white transition-colors shadow-md"
          aria-label="Start recording"
        >
          <Mic className="w-5 h-5" />
        </button>
      )}

      {/* Waveform display */}
      {(isRecording || hasRecording) && (
        <div className="flex-1 min-w-[200px] max-w-[400px] h-12 bg-white border-2 border-gray-200 rounded-xl px-4 flex items-center overflow-hidden shadow-sm">
          <div className="flex items-end gap-[2px] h-full w-full justify-center">
            {bars.map((height, index) => (
              <div
                key={index}
                className={`w-[3px] rounded-sm transition-all duration-100 ${
                  isRecording
                    ? 'bg-gradient-to-t from-purple-600 to-purple-400'
                    : hasRecording
                      ? 'bg-gradient-to-t from-green-600 to-green-400'
                      : 'bg-gray-300'
                }`}
                style={{
                  height: `${height}px`,
                  opacity: isRecording ? 0.6 + (audioLevel * 0.4) : 0.7
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Control buttons when recording or finished */}
      {(isRecording || hasRecording) && (
        <div className="flex items-center gap-2">
          <button
            onClick={acceptRecording}
            className="p-3 rounded-full bg-green-500 hover:bg-green-600 text-white transition-colors shadow-md"
            aria-label="Accept recording"
          >
            <Check className="w-5 h-5" />
          </button>
          <button
            onClick={cancelRecording}
            className="p-3 rounded-full bg-red-500 hover:bg-red-600 text-white transition-colors shadow-md"
            aria-label="Cancel recording"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Status text */}
      <div className="text-sm text-gray-600 min-w-[100px]">
        {isRecording && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            Recording...
          </div>
        )}
        {hasRecording && !isRecording && (
          <span className="text-green-600">Ready to send</span>
        )}
        {!isRecording && !hasRecording && (
          <span>Click to record</span>
        )}
      </div>

      {permissionDenied && (
        <div className="absolute top-full left-0 right-0 mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">
            Microphone permission denied. Please enable it in your browser settings.
          </p>
        </div>
      )}
    </div>
  )
}

// Demo component to test the recorder
function VoiceRecorderDemo() {
  const [recordings, setRecordings] = useState<string[]>([])

  const handleAccept = (blob: Blob) => {
    console.log('Recording accepted:', blob)
    const url = URL.createObjectURL(blob)
    setRecordings(prev => [...prev, url])
  }

  const handleCancel = () => {
    console.log('Recording cancelled')
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Voice Recorder Component</h1>
        <p className="text-gray-600">Test the voice recorder with real-time waveform visualization</p>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold mb-3">Inline Version</h2>
          <VoiceRecorder
            onAccept={handleAccept}
            onCancel={handleCancel}
            inline={true}
          />
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-3">Standard Version</h2>
          <VoiceRecorder
            onAccept={handleAccept}
            onCancel={handleCancel}
            inline={false}
          />
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-3">Auto-Start Version</h2>
          <VoiceRecorder
            onAccept={handleAccept}
            onCancel={handleCancel}
            autoStart={false}
            inline={true}
          />
          <p className="text-sm text-gray-500 mt-2">Change autoStart to true to test auto-recording</p>
        </div>
      </div>

      {recordings.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-3">Recorded Audio</h3>
          <div className="space-y-2">
            {recordings.map((url, index) => (
              <div key={index} className="p-3 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Recording {index + 1}</p>
                <audio controls src={url} className="w-full">
                  Your browser does not support the audio element.
                </audio>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg">
        <p className="font-medium mb-2">How to test:</p>
        <ul className="space-y-1">
          <li>• Click the microphone button to start recording</li>
          <li>• Speak into your microphone to see the waveforms animate</li>
          <li>• Click the check mark to accept or X to cancel</li>
          <li>• Accepted recordings will appear in the playback section below</li>
        </ul>
      </div>
    </div>
  )
}
