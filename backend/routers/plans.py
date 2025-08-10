from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Plan, Repository
from schemas import Plan as PlanSchema
from schemas import PlanCreate, PlanUpdate
from services.claude_service import _query_claude_stream

router = APIRouter(prefix="/api", tags=["plans"])


@router.get("/repositories/{repo_id}/plans", response_model=List[PlanSchema])
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


async def generate_dynamic_plan_name(repository_path: str, description: str) -> str:
    """Generate a dynamic plan name using Claude Code based on repository context and description."""
    prompt = f"""
Based on the repository at {repository_path} and this description: "{description}"

Generate a concise, descriptive name (2-4 words) for this development plan. 
The name should capture the core feature or component being planned.

Examples:
- "User Authentication System"
- "Real-time Chat Feature"
- "Payment Gateway Integration" 
- "Dashboard Analytics Panel"

Respond with only the name, no quotes or extra text.
"""
    
    try:
        chunks = []
        async for chunk in _query_claude_stream(
            working_directory=repository_path,
            system_prompt=None,
            prompt=prompt,
        ):
            if chunk:
                chunks.append(chunk)
        
        generated_name = "".join(chunks).strip()
        # Fallback if generation fails
        return generated_name if generated_name else "New Feature Plan"
    except Exception:
        return "New Feature Plan"


@router.post("/repositories/{repo_id}/plans", response_model=PlanSchema)
async def create_plan(repo_id: str, plan_data: PlanCreate, db: AsyncSession = Depends(get_db)):
    # Check if repository exists
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Generate dynamic name if plan name is temporary/generic
    plan_dict = plan_data.model_dump()
    if plan_dict.get("name") in ["New Plan", "", None] or not plan_dict.get("name"):
        description = plan_dict.get("description", "")
        if description:  # Only generate name if there's a description
            dynamic_name = await generate_dynamic_plan_name(repository.path, description)
            plan_dict["name"] = dynamic_name
        else:
            plan_dict["name"] = "New Plan"  # Fallback name
    
    plan_dict["repository_id"] = repo_id
    plan = Plan(**plan_dict)
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/plans/{plan_id}", response_model=PlanSchema)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/plans/{plan_id}", response_model=PlanSchema)
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


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
    return {"message": "Plan deleted successfully"}


@router.get("/plans/{plan_id}/versions", response_model=List[PlanSchema])
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
