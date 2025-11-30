"""
Database Setup and Session Management
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

# Create database engine
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ForecastLog(Base):
    """Model for forecast_logs table"""
    __tablename__ = "forecast_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    task_description = Column(Text, nullable=False)
    tools_used = Column(JSON)
    execution_time_seconds = Column(DECIMAL(10, 2))
    forecast_output = Column(JSON, nullable=False)
    llm_provider = Column(String(50))
    status = Column(String(20), default="success")
    error_message = Column(Text)


class FinancialMetric(Base):
    """Model for financial_metrics table"""
    __tablename__ = "financial_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_log_id = Column(Integer)
    quarter = Column(String(10))
    year = Column(Integer)
    total_revenue = Column(DECIMAL(20, 2))
    net_profit = Column(DECIMAL(20, 2))
    operating_margin = Column(DECIMAL(5, 2))
    revenue_growth = Column(DECIMAL(5, 2))
    extracted_at = Column(TIMESTAMP, default=datetime.utcnow)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)