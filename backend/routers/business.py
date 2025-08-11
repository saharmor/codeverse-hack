import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Plan, Repository

# ChatMessage schema available if needed for future use
from services.claude_service import generate_plan

router = APIRouter(prefix="/api/business", tags=["business-logic"])
logger = logging.getLogger("codeverse.business")


@router.post("/plans/{plan_id}/generate")
async def generate_plan_endpoint(plan_id: str, request_data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
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
    plan_draft_text = None
    plan_curr_draft_text = request_data.get("plan_artifact")
    if plan_curr_draft_text:
        plan_draft_text = plan_curr_draft_text
    else:
        plan_draft_text = None

    # Get chat history
    chat_override = request_data.get("chat_messages")
    # Always initialize to avoid free variable closure errors
    prev_clarifying_questions = None
    if chat_override:
        for message in reversed(chat_override):
            if isinstance(message, dict) and message.get("role") == "assistant":
                prev_clarifying_questions = message.get("content", "")
                break

    logger.info(
        "plan.generate start plan_id=%s repo_path=%s msg_len=%d has_draft=%s has_prev_questions=%s",
        plan_id,
        str(repository.path),
        len(user_message or ""),
        bool(plan_draft_text),
        bool(prev_clarifying_questions),
    )

    # Stream the response from Claude
    async def stream_response():
        try:
            chunk_count = 0
            totals: Dict[str, int] = {"plan": 0, "clarify_questions": 0, "plan_name": 0}
            async for output_type, chunk in generate_plan(
                project_dir=repository.path,
                user_raw_notes=user_message,
                prev_clarifying_questions=prev_clarifying_questions,
                current_plan=plan_draft_text,
            ):
                # Send each chunk in the requested format
                chunk_data = {"chunk": chunk, "output_type": output_type.value}
                chunk_count += 1
                totals[output_type.value] = totals.get(output_type.value, 0) + len(chunk or "")
                if chunk_count % 10 == 0:
                    logger.debug(
                        "plan.generate stream plan_id=%s count=%d last_type=%s last_size=%d",
                        plan_id,
                        chunk_count,
                        output_type.value,
                        len(chunk or ""),
                    )
                yield f"data: {json.dumps(chunk_data)}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            logger.info(
                "plan.generate complete plan_id=%s chunks=%d sizes=%s",
                plan_id,
                chunk_count,
                totals,
            )

        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            logger.exception("plan.generate error plan_id=%s: %s", plan_id, e)
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
