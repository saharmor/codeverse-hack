import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Plan, PlanVersion, Repository
from services.claude_prompts import ClaudeOutputType

# ChatMessage schema available if needed for future use
from services.claude_service import generate_plan

router = APIRouter(prefix="/api/business", tags=["business-logic"])


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
    if chat_override:
        for message in reversed(chat_override):
            if isinstance(message, dict) and message.get("role") == "assistant":
                prev_clarifying_questions = message.get("content", "")
                break
    else:
        prev_clarifying_questions = None

    # Stream the response from Claude and accumulate plan content
    async def stream_response():
        accumulated_plan_content = ""
        try:
            claude_generated_content = False
            async for output_type, chunk in generate_plan(
                project_dir=repository.path,
                user_raw_notes=user_message,
                prev_clarifying_questions=prev_clarifying_questions,
                current_plan=plan_draft_text,
            ):
                claude_generated_content = True
                # Accumulate plan content for saving later
                if output_type == ClaudeOutputType.PLAN:
                    accumulated_plan_content += chunk

                # Send each chunk in the requested format
                chunk_data = {"chunk": chunk, "output_type": output_type.value}
                yield f"data: {json.dumps(chunk_data)}\n\n"

            # If no content was generated, provide a fallback
            if not claude_generated_content:
                fallback_plan = f"# Plan for {plan.name}\n\n## Overview\nImplementation plan is being generated.\n\n## Next Steps\n1. Review requirements\n2. Design architecture\n3. Implement features\n4. Add testing"
                accumulated_plan_content = fallback_plan

                chunk_data = {"chunk": fallback_plan, "output_type": ClaudeOutputType.PLAN.value}
                yield f"data: {json.dumps(chunk_data)}\n\n"

            # Save the accumulated plan content as a new version if we have content
            if accumulated_plan_content.strip():
                # Get the next version number
                result = await db.execute(
                    select(PlanVersion)
                    .where(PlanVersion.plan_id == plan_id)
                    .order_by(desc(PlanVersion.version))
                    .limit(1)
                )
                latest_version = result.scalar_one_or_none()
                next_version = (latest_version.version + 1) if latest_version else 1
                # Create new plan version
                new_version = PlanVersion(
                    plan_id=plan_id, content=accumulated_plan_content.strip(), version=next_version
                )
                db.add(new_version)
                await db.commit()
                await db.refresh(new_version)

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
