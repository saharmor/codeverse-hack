from __future__ import annotations

import asyncio
import base64
import io
import time
import traceback
import wave

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import Plan
from schemas import TranscribeRequest, TranscribeResponse

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


router = APIRouter(prefix="/api", tags=["transcribe"])


def _decode_wav_info(audio_b64: str) -> tuple[bytes, dict]:
    try:
        audio_bytes = base64.b64decode(audio_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 audio")

    if len(audio_bytes) > settings.MAX_AUDIO_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio too large")

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / float(framerate) if framerate else 0.0
            comptype = wf.getcomptype()
            compname = wf.getcompname()
    except wave.Error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid WAV file")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio decode error")

    if duration <= 0 or duration > settings.MAX_AUDIO_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio duration out of range",
        )

    return audio_bytes, {
        "channels": n_channels,
        "sample_width": sampwidth,
        "sample_rate": framerate,
        "frames": n_frames,
        "duration": duration,
        "compression": f"{comptype}:{compname}",
        "size_bytes": len(audio_bytes),
    }


async def _transcribe_with_openai(audio_bytes: bytes, prompt: str | None = None) -> dict:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="STT provider misconfigured")
    if OpenAI is None:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="STT provider not available")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def run_call():
        def _call():
            try:
                bio = io.BytesIO(audio_bytes)
                try:
                    bio.name = "audio.wav"  # type: ignore[attr-defined]
                except Exception:
                    pass
                result = client.audio.transcriptions.create(
                    model=settings.OPENAI_STT_MODEL,
                    file=bio,
                    language="en",
                    prompt=prompt or "",
                )
                return {
                    "text": getattr(result, "text", ""),
                    "confidence": getattr(result, "confidence", None),
                }
            except Exception as e:  # rethrown in async context
                raise e

        try:
            return await asyncio.to_thread(_call)
        except Exception as e:
            print({"event": "stt_error", "message": str(e)})
            traceback.print_exc()
            if settings.DEBUG:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"STT provider error: {e}",
                )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="STT provider error")

    try:
        return await asyncio.wait_for(run_call(), timeout=settings.STT_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Transcription timed out")


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Plan).where(Plan.id == req.plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        t0 = time.perf_counter()
        audio_bytes, info = _decode_wav_info(req.audio_wav_base64)

        prompt = "Use developer punctuation. Keep exact case for identifiers and file paths."

        stt0 = time.perf_counter()
        data = await _transcribe_with_openai(audio_bytes, prompt=prompt)
        stt_latency_ms = int((time.perf_counter() - stt0) * 1000)

        raw_text = data.get("text", "").strip()
        confidence = data.get("confidence")
        latency_ms = int((time.perf_counter() - t0) * 1000)

        print(
            {
                "event": "transcribe",
                "plan_id": req.plan_id,
                "audio": {
                    "duration": round(info["duration"], 3),
                    "size_bytes": info["size_bytes"],
                    "channels": info["channels"],
                    "sample_rate": info["sample_rate"],
                },
                "stt": {
                    "model": settings.OPENAI_STT_MODEL,
                    "latency_ms": stt_latency_ms,
                },
                "overall_latency_ms": latency_ms,
            }
        )

        return TranscribeResponse(
            raw_text=raw_text,
            corrected_text=None,
            confidence=confidence,
            vocab_hit_rate=0.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        print({"event": "transcribe_error", "message": str(e)})
        traceback.print_exc()
        if settings.DEBUG:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Transcribe error: {e}",
            )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="STT provider error")
