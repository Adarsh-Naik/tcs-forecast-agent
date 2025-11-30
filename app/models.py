"""
Pydantic Models for API Request/Response
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ForecastRequest(BaseModel):
    """Request model for forecast generation"""
    task: str = Field(
        ...,
        description="The analytical task description",
        example="Analyze the last 3 quarters and provide a forecast for Q4"
    )


class FinancialTrend(BaseModel):
    """Financial trend information"""
    metric: str
    trend: str  # "increasing", "decreasing", "stable"
    percentage_change: Optional[float] = None
    analysis: str


class ManagementOutlook(BaseModel):
    """Management outlook and sentiment"""
    sentiment: str  # "positive", "negative", "neutral"
    key_statements: List[str]
    strategic_focus: List[str]


class RiskOpportunity(BaseModel):
    """Risk or opportunity identified"""
    type: str  # "risk" or "opportunity"
    description: str
    potential_impact: str  # "high", "medium", "low"


class ForecastOutput(BaseModel):
    """Structured forecast output"""
    summary: str
    financial_trends: List[FinancialTrend]
    management_outlook: ManagementOutlook
    risks_and_opportunities: List[RiskOpportunity]
    quarterly_forecast: str
    confidence_level: str  # "high", "medium", "low"
    data_sources_used: List[str]


class ForecastResponse(BaseModel):
    """API response model"""
    status: str
    timestamp: datetime
    execution_time_seconds: float
    tools_used: List[str]
    forecast: ForecastOutput
    log_id: int