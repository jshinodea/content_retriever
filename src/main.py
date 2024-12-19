"""
Content Retriever - Main Application Entry Point

This module initializes and runs the FastAPI application that serves the content retrieval system.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.routes import router

app = FastAPI(
    title="Content Retriever",
    description="AI-powered content webscraping agent",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

# Include API routes
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    ) 