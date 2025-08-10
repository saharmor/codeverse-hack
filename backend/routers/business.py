import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ChatSession, Plan, PlanVersion, Repository

# ChatMessage schema available if needed for future use
from services.claude_service import generate_plan_business

router = APIRouter(prefix="/api/business", tags=["business-logic"])


@router.post("/plans/{plan_id}/generate")
async def generate_plan_endpoint(plan_id: str, request_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Main business logic endpoint for plan generation.

    Expected request_data:
    {
        "user_message": "string - latest user question/response",
        "plan_artifact": {...} - current plan artifact (optional),
        "chat_messages": [...] - recent chat history (optional)
    }
    """

    # Validate request data
    user_message = request_data.get("user_message")
    if not user_message:
        raise HTTPException(status_code=400, detail="user_message is required")

    # Get the plan
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get the repository
    result = await db.execute(select(Repository).where(Repository.id == plan.repository_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get existing plan artifact (if any)
    existing_artifact = None
    artifact_override = request_data.get("plan_artifact")
    if artifact_override:
        existing_artifact = artifact_override
    else:
        result = await db.execute(select(PlanVersion).where(PlanVersion.plan_id == plan_id))
        artifact = result.scalar_one_or_none()
        if artifact:
            existing_artifact = artifact.content

    # Get chat history
    chat_history = []
    chat_override = request_data.get("chat_messages")
    if chat_override:
        chat_history = chat_override
    else:
        result = await db.execute(select(ChatSession).where(ChatSession.plan_id == plan_id))
        chat_session = result.scalar_one_or_none()
        if chat_session and chat_session.messages:
            chat_history = chat_session.messages

    # Prepare data for generate_plan function
    plan_context = {
        "plan": plan,
        "repository": repository,
        "existing_artifact": existing_artifact,
        "chat_history": chat_history,
        "user_message": user_message,
    }

    # Stream the response from Claude
    async def stream_response():
        try:
            async for chunk in generate_plan_business(plan_context):
                # Send each chunk as JSON
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )
