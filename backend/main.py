import asyncio
import base64
import io
import time
import traceback
import wave
from datetime import datetime
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import ChatSession, Plan, PlanArtifact, Repository
from schemas import ChatSession as ChatSessionSchema
from schemas import ChatSessionCreate, ChatSessionUpdate
from schemas import Plan as PlanSchema
from schemas import PlanArtifact as PlanArtifactSchema
from schemas import PlanArtifactCreate, PlanCreate, PlanUpdate
from schemas import Repository as RepositorySchema
from schemas import RepositoryCreate, RepositoryUpdate, TranscribeRequest, TranscribeResponse

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional import error at runtime
    OpenAI = None  # type: ignore

app = FastAPI(
    title="CodeVerse API",
    description="Smart code planning with Claude Code",
    version=settings.VERSION,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to CodeVerse API!"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "CodeVerse API",
        "version": settings.VERSION,
        "stt_configured": bool(settings.OPENAI_API_KEY),
        "stt_model": settings.OPENAI_STT_MODEL,
    }


# Repository endpoints
@app.get("/api/repositories", response_model=List[RepositorySchema])
async def get_repositories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository))
    repositories = result.scalars().all()
    return repositories


@app.post("/api/repositories", response_model=RepositorySchema)
async def create_repository(repo_data: RepositoryCreate, db: AsyncSession = Depends(get_db)):
    repository = Repository(**repo_data.model_dump())
    db.add(repository)
    await db.commit()
    await db.refresh(repository)
    return repository


@app.get("/api/repositories/{repo_id}", response_model=RepositorySchema)
async def get_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


@app.put("/api/repositories/{repo_id}", response_model=RepositorySchema)
async def update_repository(repo_id: str, repo_data: RepositoryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    for field, value in repo_data.model_dump(exclude_unset=True).items():
        setattr(repository, field, value)

    await db.commit()
    await db.refresh(repository)
    return repository


@app.delete("/api/repositories/{repo_id}")
async def delete_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repository)
    await db.commit()
    return {"message": "Repository deleted successfully"}


# Plan endpoints
@app.get("/api/repositories/{repo_id}/plans", response_model=List[PlanSchema])
async def get_repository_plans(repo_id: str, db: AsyncSession = Depends(get_db)):
    # First check if repository exists
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get plans for this repository
    result = await db.execute(select(Plan).where(Plan.repository_id == repo_id))
    plans = result.scalars().all()
    return plans


@app.post("/api/repositories/{repo_id}/plans", response_model=PlanSchema)
async def create_plan(repo_id: str, plan_data: PlanCreate, db: AsyncSession = Depends(get_db)):
    # Check if repository exists
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Create plan with repository_id
    plan_dict = plan_data.model_dump()
    plan_dict["repository_id"] = repo_id
    plan = Plan(**plan_dict)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@app.get("/api/plans/{plan_id}", response_model=PlanSchema)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.put("/api/plans/{plan_id}", response_model=PlanSchema)
async def update_plan(plan_id: str, plan_data: PlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in plan_data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)
    return plan


@app.delete("/api/plans/{plan_id}")
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
    return {"message": "Plan deleted successfully"}


@app.get("/api/plans/{plan_id}/versions", response_model=List[PlanSchema])
async def get_plan_versions(plan_id: str, db: AsyncSession = Depends(get_db)):
    # Get the plan first to find repository_id and name
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get all versions of this plan
    result = await db.execute(
        select(Plan).where(Plan.repository_id == plan.repository_id, Plan.name == plan.name).order_by(Plan.version)
    )
    versions = result.scalars().all()
    return versions


# Plan Artifact endpoints
@app.get("/api/plans/{plan_id}/artifacts", response_model=List[PlanArtifactSchema])
async def get_plan_artifacts(plan_id: str, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get artifacts for this plan
    result = await db.execute(select(PlanArtifact).where(PlanArtifact.plan_id == plan_id))
    artifacts = result.scalars().all()
    return artifacts


@app.post("/api/plans/{plan_id}/artifacts", response_model=PlanArtifactSchema)
async def create_plan_artifact(plan_id: str, artifact_data: PlanArtifactCreate, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Create artifact with plan_id
    artifact_dict = artifact_data.model_dump()
    artifact_dict["plan_id"] = plan_id
    artifact = PlanArtifact(**artifact_dict)
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return artifact


@app.get("/api/artifacts/{artifact_id}", response_model=PlanArtifactSchema)
async def get_plan_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanArtifact).where(PlanArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.delete("/api/artifacts/{artifact_id}")
async def delete_plan_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanArtifact).where(PlanArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    await db.delete(artifact)
    await db.commit()
    return {"message": "Artifact deleted successfully"}


# Chat Session endpoints
@app.get("/api/plans/{plan_id}/chat", response_model=ChatSessionSchema)
async def get_plan_chat(plan_id: str, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get chat session for this plan (there should be only one active)
    result = await db.execute(select(ChatSession).where(ChatSession.plan_id == plan_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat


@app.post("/api/plans/{plan_id}/chat", response_model=ChatSessionSchema)
async def create_chat_session(plan_id: str, chat_data: ChatSessionCreate, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Create chat session with plan_id
    chat_dict = chat_data.model_dump()
    chat_dict["plan_id"] = plan_id
    chat = ChatSession(**chat_dict)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


# --- Transcription Endpoint ---
def _decode_wav_info(audio_b64: str):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio duration out of range")

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

    # Use asyncio timeout to bound provider time
    async def run_call():
        # Run sync SDK call in a thread to avoid blocking event loop
        def _call():
            try:
                # Use an in-memory BytesIO with a name attribute so SDK treats it as a file
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
                return {"text": getattr(result, "text", ""), "confidence": getattr(result, "confidence", None)}
            except Exception as e:  # wrapped and rethrown in async context
                raise e

        try:
            return await asyncio.to_thread(_call)
        except Exception as e:
            # Log the exception and traceback for debugging while returning a sanitized error to client
            print({"event": "stt_error", "message": str(e)})
            traceback.print_exc()
            if settings.DEBUG:
                # surface a little more detail in debug mode
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"STT provider error: {e}")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="STT provider error") from e

    try:
        return await asyncio.wait_for(run_call(), timeout=settings.STT_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Transcription timed out")


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Validate plan exists
        result = await db.execute(select(Plan).where(Plan.id == req.plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        t0 = time.perf_counter()
        audio_bytes, info = _decode_wav_info(req.audio_wav_base64)

        # Minimal prompt for now (no vocab)
        prompt = "Use developer punctuation. Keep exact case for identifiers and file paths."

        stt0 = time.perf_counter()
        data = await _transcribe_with_openai(audio_bytes, prompt=prompt)
        stt_latency_ms = int((time.perf_counter() - stt0) * 1000)

        raw_text = data.get("text", "").strip()
        confidence = data.get("confidence")

        latency_ms = int((time.perf_counter() - t0) * 1000)

        # Structured log
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
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Transcribe error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="STT provider error")


@app.put("/api/chat/{chat_id}", response_model=ChatSessionSchema)
async def update_chat_session(chat_id: str, chat_data: ChatSessionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")

    for field, value in chat_data.model_dump(exclude_unset=True).items():
        setattr(chat, field, value)

    await db.commit()
    await db.refresh(chat)
    return chat


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
    )
