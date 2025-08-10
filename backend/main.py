from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import artifacts, business, chat, plans, repositories

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
app.include_router(artifacts.router)
app.include_router(chat.router)
app.include_router(business.router)


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
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
    )
