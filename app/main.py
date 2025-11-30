"""
FastAPI Application - Main Entry Point
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import time
import logging

from app.config import settings
from app.database import get_db, init_db, ForecastLog
from app.models import ForecastRequest, ForecastResponse, ForecastOutput
from agent.orchestrator import ForecastOrchestrator
from utils.llm_provider import get_provider_name

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TCS Financial Forecasting Agent",
    description="AI-powered business outlook forecasting for Tata Consultancy Services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database and agent on startup"""
    logger.info("Initializing application...")
    init_db()
    logger.info(f"Using LLM provider: {get_provider_name()}")
    logger.info("Application ready")


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "TCS Financial Forecasting Agent",
        "llm_provider": get_provider_name()
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_provider": get_provider_name(),
        "database": "connected"
    }


@app.post("/forecast", response_model=ForecastResponse)
def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a financial forecast for TCS
    
    This endpoint orchestrates the AI agent to:
    1. Extract financial metrics from quarterly reports
    2. Analyze earnings call transcripts
    3. Generate a structured forecast
    
    Args:
        request: Forecast request with task description
        db: Database session
    
    Returns:
        Structured forecast with execution metadata
    """
    start_time = time.time()
    
    try:
        logger.info(f"Received forecast request: {request.task[:100]}...")
        
        # Initialize orchestrator
        orchestrator = ForecastOrchestrator()
        
        # Generate forecast
        result = orchestrator.generate_forecast(request.task)
        
        execution_time = time.time() - start_time
        
        # Validate and parse forecast
        forecast_data = result["forecast"]
        tools_used = result["tools_used"]
        
        # Create forecast output model
        forecast_output = ForecastOutput(**forecast_data)
        
        # Log to database
        log_entry = ForecastLog(
            task_description=request.task,
            tools_used=tools_used,
            execution_time_seconds=round(execution_time, 2),
            forecast_output=forecast_data,
            llm_provider=get_provider_name(),
            status="success"
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        logger.info(f"Forecast generated successfully in {execution_time:.2f}s")
        
        # Return response
        return ForecastResponse(
            status="success",
            timestamp=datetime.utcnow(),
            execution_time_seconds=round(execution_time, 2),
            tools_used=tools_used,
            forecast=forecast_output,
            log_id=log_entry.id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Error generating forecast: {e}", exc_info=True)
        
        # Log error to database
        try:
            error_log = ForecastLog(
                task_description=request.task,
                tools_used=[],
                execution_time_seconds=round(execution_time, 2),
                forecast_output={"error": str(e)},
                llm_provider=get_provider_name(),
                status="error",
                error_message=str(e)
            )
            db.add(error_log)
            db.commit()
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
def get_logs(limit: int = 10, db: Session = Depends(get_db)):
    """
    Retrieve recent forecast logs
    
    Args:
        limit: Number of logs to retrieve
        db: Database session
    
    Returns:
        List of recent forecast logs
    """
    logs = db.query(ForecastLog).order_by(
        ForecastLog.request_timestamp.desc()
    ).limit(limit).all()
    
    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "timestamp": log.request_timestamp.isoformat(),
                "task": log.task_description[:100] + "...",
                "status": log.status,
                "execution_time": float(log.execution_time_seconds),
                "tools_used": log.tools_used
            }
            for log in logs
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)