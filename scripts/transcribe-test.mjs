#!/usr/bin/env node

// Minimal script: read WAV file, print base64 to console, call /api/transcribe

import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function parseArgs(argv) {
  const args = {}
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i]
    const next = argv[i + 1]
    if (a.startsWith('--')) {
      const key = a.slice(2)
      if (typeof next === 'string' && !next.startsWith('--')) {
        args[key] = next
        i++
      } else {
        args[key] = true
      }
    }
  }
  return args
}

async function main() {
  const args = parseArgs(process.argv)
  const defaultFile = path.join(__dirname, 'audio-test.wav')
  const filePath = args['file'] || args['f'] || defaultFile
  const planId = args['plan-id'] || args['plan']
  const apiUrl = (args['api-url'] || 'http://localhost:8000').replace(/\/$/, '')
  const endpoint = args['endpoint'] || '/api/transcribe'
  const printBase64 = args['print-base64'] !== 'false'

  if (!planId) {
    console.error('Usage: node scripts/transcribe-test.mjs --plan-id <PLAN_ID> [--file /absolute/path/audio.wav] [--api-url http://localhost:8000] [--endpoint /api/transcribe] [--print-base64 true|false]')
    process.exit(1)
  }

  const absPath = path.isAbsolute(filePath) ? filePath : path.resolve(process.cwd(), filePath)
  if (filePath === defaultFile) {
    console.log(`Using default audio file: ${absPath}`)
  }
  const buf = await fs.readFile(absPath)

  // Basic WAV check (RIFF/WAVE)
  const header = buf.subarray(0, 12).toString('ascii')
  if (!(header.startsWith('RIFF') && header.includes('WAVE'))) {
    console.warn('Warning: file does not look like a WAV (RIFF/WAVE header missing). The server will reject non-WAV.')
  }

  const b64 = buf.toString('base64')

  console.log('--- WAV Base64 (length: ' + b64.length + ') ---')
  if (printBase64) {
    console.log(b64)
  } else {
    console.log(b64.slice(0, 120) + '...')
  }
  console.log('--- End Base64 ---')

  const url = apiUrl + endpoint
  console.log('POST', url)
  const body = { plan_id: planId, audio_wav_base64: b64 }

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const text = await res.text()
    let data
    try { data = JSON.parse(text) } catch { data = text }
    console.log('Status:', res.status)
    console.log('Response:', data)
    if (!res.ok) process.exit(2)
  } catch (err) {
    console.error('Request failed:', err)
    process.exit(3)
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(4)
})
