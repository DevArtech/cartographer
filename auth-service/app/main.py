import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.auth import router as auth_router
from .services.usage_middleware import UsageTrackingMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cartographer Auth Service",
        description="User authentication and authorization microservice for Cartographer",
        version="0.1.0"
    )

    # Allow CORS for development and integration with main app
    allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Usage tracking middleware - reports endpoint usage to metrics service
    app.add_middleware(UsageTrackingMiddleware, service_name="auth-service")

    # Include routers
    app.include_router(auth_router, prefix="/api/auth")

    @app.get("/")
    def root():
        return {
            "service": "Cartographer Auth Service",
            "status": "running",
            "version": "0.1.0"
        }

    @app.get("/healthz")
    def healthz():
        """Health check endpoint for container orchestration"""
        return {"status": "healthy"}

    return app


app = create_app()
