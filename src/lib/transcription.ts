import { ApiClient } from './api'

const api = new ApiClient()

async function blobToWavBase64(blob: Blob): Promise<string> {
  // If the blob is already WAV, just base64 encode
  if (blob.type === 'audio/wav' || blob.type === 'audio/x-wav') {
    const arrayBuffer = await blob.arrayBuffer()
    const bytes = new Uint8Array(arrayBuffer)
    let binary = ''
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
    return btoa(binary)
  }
  // Otherwise, rely on server validation to reject non-WAV per spec
  const arrayBuffer = await blob.arrayBuffer()
  const bytes = new Uint8Array(arrayBuffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

export async function transcribeAudio(planId: string, blob: Blob): Promise<{
  raw_text: string
  corrected_text: string | null
  confidence: number | null
  vocab_hit_rate: number
}> {
  const audio_wav_base64 = await blobToWavBase64(blob)

  // Debug logging (controlled by env flag)
  try {
    const debug = process.env.NEXT_PUBLIC_DEBUG === 'true'
    if (debug) {
      console.log('Transcription debug — blob:', { type: blob.type, size: blob.size })
      console.log('Transcription debug — base64 length:', audio_wav_base64.length)
      console.log('Transcription debug — base64:', audio_wav_base64)
    }
  } catch {}

  const res = await (api as any).request('/api/transcribe', {
    method: 'POST',
    body: JSON.stringify({ plan_id: planId, audio_wav_base64 }),
  } as any)
  if (res.error) {
    const err: any = new Error(res.error)
    if (res.errorDetails) err.details = res.errorDetails
    throw err
  }
  return res.data
}
