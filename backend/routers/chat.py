from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ChatSession, Plan
from schemas import ChatSession as ChatSessionSchema
from schemas import ChatSessionCreate, ChatSessionUpdate

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/plans/{plan_id}/chat", response_model=ChatSessionSchema)
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


@router.post("/plans/{plan_id}/chat", response_model=ChatSessionSchema)
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


@router.put("/chat/{chat_id}", response_model=ChatSessionSchema)
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
