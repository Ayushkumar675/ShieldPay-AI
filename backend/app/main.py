"""
ShieldPay AI — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.models.database import connect_db, close_db
from app.api import workers, policies, claims, premium, fraud, integrations, payments, analytics
from app.api.ai_routes import router as ai_router, load_ai_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Load AI/ML models
    print("\nLoading AI/ML Models...")
    load_ai_models()

    # Connect database
    await connect_db()
    
    # Initialize platform metrics if they don't exist
    from app.services.liquidity_engine import LiquidityEngineService
    await LiquidityEngineService.get_state()
    
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered parametric micro-insurance for delivery workers — income loss protection",
    lifespan=lifespan,
)

# CORS
import os
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
cors_origins_list = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(workers.router, prefix="/api/v1/workers", tags=["Workers"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["Policies"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["Claims"])
app.include_router(premium.router, prefix="/api/v1/premium", tags=["Premium"])
app.include_router(fraud.router, prefix="/api/v1/fraud", tags=["Fraud Analytics"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
from app.api import simulation
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["Simulation"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["External Integrations"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Intelligence"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "description": "Parametric micro-insurance for e-commerce delivery workers",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}
