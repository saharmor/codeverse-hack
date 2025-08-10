from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Plan, PlanVersion
from schemas import PlanVersion as PlanVersionSchema
from schemas import PlanVersionCreate

router = APIRouter(prefix="/api", tags=["plan_versions"])


@router.get("/plans/{plan_id}/plan_versions", response_model=List[PlanVersionSchema])
async def get_plan_versions(plan_id: str, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Get plan versions for this plan
    result = await db.execute(select(PlanVersion).where(PlanVersion.plan_id == plan_id))
    plan_versions = result.scalars().all()
    return plan_versions


@router.post("/plans/{plan_id}/plan_versions", response_model=PlanVersionSchema)
async def create_plan_version(plan_id: str, version_data: PlanVersionCreate, db: AsyncSession = Depends(get_db)):
    # Check if plan exists
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Create plan version with plan_id
    version_dict = version_data.model_dump()
    version_dict["plan_id"] = plan_id
    plan_version = PlanVersion(**version_dict)
    db.add(plan_version)
    await db.commit()
    await db.refresh(plan_version)
    return plan_version


@router.get("/plan_versions/{version_id}", response_model=PlanVersionSchema)
async def get_plan_version(version_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanVersion).where(PlanVersion.id == version_id))
    plan_version = result.scalar_one_or_none()
    if not plan_version:
        raise HTTPException(status_code=404, detail="Plan version not found")
    return plan_version


@router.delete("/plan_versions/{version_id}")
async def delete_plan_version(version_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanVersion).where(PlanVersion.id == version_id))
    plan_version = result.scalar_one_or_none()
    if not plan_version:
        raise HTTPException(status_code=404, detail="Plan version not found")

    await db.delete(plan_version)
    await db.commit()
    return {"message": "Plan version deleted successfully"}
