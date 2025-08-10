from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Plan, PlanArtifact
from schemas import PlanArtifact as PlanArtifactSchema
from schemas import PlanArtifactCreate

router = APIRouter(prefix="/api", tags=["artifacts"])


@router.get("/plans/{plan_id}/artifacts", response_model=List[PlanArtifactSchema])
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


@router.post("/plans/{plan_id}/artifacts", response_model=PlanArtifactSchema)
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


@router.get("/artifacts/{artifact_id}", response_model=PlanArtifactSchema)
async def get_plan_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanArtifact).where(PlanArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.delete("/artifacts/{artifact_id}")
async def delete_plan_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlanArtifact).where(PlanArtifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    await db.delete(artifact)
    await db.commit()
    return {"message": "Artifact deleted successfully"}
