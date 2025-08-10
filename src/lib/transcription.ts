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
  const res = await api['request']<any>('/api/transcribe', {
    method: 'POST',
    body: JSON.stringify({ plan_id: planId, audio_wav_base64 }),
  } as any)
  if (res.error) throw new Error(res.error)
  return res.data
}
