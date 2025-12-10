"""
CrowdStrike AI Pipeline Health Monitor - FastAPI Application

Main entry point for the backend API server.
Provides health checks, incident management, and infrastructure monitoring.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db, SessionLocal, seed_demo_data
from app.api import health, incidents, infrastructure


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print("🚀 Starting CrowdStrike AI Pipeline Health Monitor...")
    init_db()
    
    # Seed demo data
    db = SessionLocal()
    try:
        seed_demo_data(db)
        print("✅ Database initialized and seeded")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="CrowdStrike AI Pipeline Health Monitor",
    description="""
    Demo application for AI/ML pipeline health monitoring, automated remediation,
    and infrastructure optimization.
    
    ## Features
    - **Health Checks**: Latency, correctness, drift, and resource monitoring
    - **Incidents**: Automatic incident creation and tracking
    - **Remediation**: Automated and manual remediation strategies
    - **Infrastructure**: Multi-cloud metrics and rightsizing recommendations
    
    ## Demo Usage
    1. View health checks at `/healthchecks`
    2. Inject failures with `/inject-failure`
    3. Monitor metrics at `/metrics`
    4. View rightsizing at `/rightsizing/report`
    """,
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, tags=["Health Checks"])
app.include_router(incidents.router, tags=["Incidents"])
app.include_router(infrastructure.router, tags=["Infrastructure"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CrowdStrike AI Pipeline Health Monitor",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "health_checks": "/healthchecks",
            "run_check": "/healthchecks/run",
            "incidents": "/incidents",
            "remediate": "/remediate",
            "metrics": "/metrics",
            "infrastructure": "/infrastructure/summary",
            "rightsizing": "/rightsizing/report"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Basic application health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True
    )
