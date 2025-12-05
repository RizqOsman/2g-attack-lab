"""
GSM C2 Dashboard - Main Application
FastAPI application entry point for Command & Control interface
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api.routes import router
from app.api.websocket import websocket_live_feed
from app.models.database import db_manager
from app.services.log_monitor import monitor_manager
from app.services.vty_client import vty_pool

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug_mode else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting GSM C2 Dashboard...")
    logger.info(f"VTY MSC Port: {settings.vty_msc_port}")
    logger.info(f"VTY BTS Port: {settings.vty_bts_port}")
    logger.info(f"HLR Database: {settings.hlr_database_path}")
    logger.info(f"Log File: {settings.osmocom_log_path}")
    
    # Verify critical files exist (non-blocking warnings)
    try:
        import os
        if not os.path.exists(settings.hlr_database_path):
            logger.warning(f"HLR database not found at {settings.hlr_database_path}")
        if not os.path.exists(settings.osmocom_log_path):
            logger.warning(f"Log file not found at {settings.osmocom_log_path}")
    except Exception as e:
        logger.warning(f"Startup check failed: {e}")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down GSM C2 Dashboard...")
    
    # Close database connections
    try:
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Stop log monitoring
    try:
        await monitor_manager.cleanup()
        logger.info("Log monitors stopped")
    except Exception as e:
        logger.error(f"Error stopping monitors: {e}")
    
    # Close VTY connections
    try:
        await vty_pool.close_all()
        logger.info("VTY connections closed")
    except Exception as e:
        logger.error(f"Error closing VTY connections: {e}")
    
    logger.info("Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="GSM C2 Dashboard",
    description="""
    **Command & Control Dashboard for GSM Laboratory**
    
    This API provides control and monitoring capabilities for a GSM security research
    laboratory using PlutoSDR and Osmocom stack.
    
    ## Features
    - Real-time subscriber monitoring
    - BTS encryption configuration (A5/0 / A5/1)
    - SMS injection capabilities
    - Live event streaming via WebSocket
    
    ## Legal Notice
    ⚠️ This application is designed for authorized security research in controlled
    laboratory environments. Ensure compliance with all applicable laws and regulations.
    
    ## Services
    - **VTY MSC**: Port 4242 - Mobile Switching Center control
    - **VTY BTS**: Port 4241 - Base Transceiver Station control
    - **HLR Database**: SQLite subscriber database
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api", tags=["API"])

# Register WebSocket endpoint
@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time event streaming"""
    await websocket_live_feed(websocket)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "GSM C2 Dashboard",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "websocket": "/ws/live-feed",
        "endpoints": {
            "status": "/api/status",
            "subscribers": "/api/subscribers",
            "encryption": "/api/config/encryption",
            "sms_spoof": "/api/attack/sms-spoof",
            "health": "/api/health"
        }
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "detail": str(exc) if settings.debug_mode else "An error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug_mode,
        log_level="debug" if settings.debug_mode else "info"
    )
