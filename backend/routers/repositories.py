from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Repository
from schemas import Repository as RepositorySchema
from schemas import RepositoryCreate, RepositoryUpdate

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("", response_model=List[RepositorySchema])
async def get_repositories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository))
    repositories = result.scalars().all()
    return repositories


@router.post("", response_model=RepositorySchema)
async def create_repository(repo_data: RepositoryCreate, db: AsyncSession = Depends(get_db)):
    repository = Repository(**repo_data.model_dump())
    db.add(repository)
    await db.commit()
    await db.refresh(repository)
    return repository


@router.get("/{repo_id}", response_model=RepositorySchema)
async def get_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


@router.put("/{repo_id}", response_model=RepositorySchema)
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


@router.delete("/{repo_id}")
async def delete_repository(repo_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repository = result.scalar_one_or_none()
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    await db.delete(repository)
    await db.commit()
    return {"message": "Repository deleted successfully"}
