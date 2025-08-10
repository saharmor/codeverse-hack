import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ChatSession, Plan, PlanVersion, Repository

# ChatMessage schema available if needed for future use
from services.claude_service import generate_plan
from services.claude_prompts import ClaudeOutputType

router = APIRouter(prefix="/api/business", tags=["business-logic"])


@router.post("/plans/{plan_id}/generate")
async def generate_plan_endpoint(plan_id: str, request_data: Dict[str, Any],
                                  db: AsyncSession = Depends(get_db)):
    """
    Main business logic endpoint for plan generation.

    Expected request_data:
    {
        "user_message": "string - latest user question/response",
        "plan_artifact": {...} - current plan artifact (optional),
        "chat_messages": [...] - recent chat history (optional),
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

    # Get existing plan version (if any)
    existing_plan_version = None
    plan_version_override = request_data.get("plan_artifact")
    if plan_version_override:
        existing_plan_version = plan_version_override
    else:
        result = await db.execute(select(PlanVersion).where(PlanVersion.plan_id == plan_id))
        artifact = result.scalar_one_or_none()
        if artifact and artifact.content:
            # Handle different content structures safely
            if isinstance(artifact.content, dict):
                existing_artifact = json.dumps(artifact.content)
            else:
                existing_artifact = str(artifact.content)

    existing_artifact = None  # TODO SAHAR test for initial plan
    
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

    # Extract previous clarifying questions from chat history
    prev_clarifying_questions = None
    # Look through chat history from most recent to oldest
    for message in reversed(chat_history):
        if (isinstance(message, dict) and 
            message.get("role") == "assistant" and 
            message.get("type") == "clarifying_questions"):
            prev_clarifying_questions = str(message.get("content", ""))
            break

    # Stream the response from Claude
    async def stream_response():
        try:
            async for output_type, chunk in generate_plan(
                project_dir=repository.path,
                user_raw_notes=user_message,
                prev_clarifying_questions=prev_clarifying_questions,
                current_plan=existing_artifact,
            ):
                # Send each chunk in the requested format
                chunk_data = {
                    "chunk": chunk,
                    "output_type": output_type.value
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"

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
