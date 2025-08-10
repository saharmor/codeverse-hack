from datetime import datetime
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import ChatSession, Plan, Repository
from routers import business, chat, plan_versions, plans, repositories, transcribe
from schemas import ChatSession as ChatSessionSchema
from schemas import ChatSessionCreate, ChatSessionUpdate
from schemas import Plan as PlanSchema
from schemas import PlanCreate, PlanUpdate
from schemas import Repository as RepositorySchema
from schemas import RepositoryCreate, RepositoryUpdate

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

# Include routers
app.include_router(repositories.router)
app.include_router(plans.router)
app.include_router(plan_versions.router)
app.include_router(chat.router)
app.include_router(business.router)
app.include_router(transcribe.router)


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
