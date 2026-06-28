from datetime import datetime
from pydantic import BaseModel, Field


class TopicCandidate(BaseModel):
    title: str = Field(..., description="Topic title")
    reason: str = Field(..., description="Why this topic matters now")
    score: float = Field(..., ge=0, le=100, description="Relevance score 0-100")


class Topic(BaseModel):
    title: str
    reason: str
    score: float
    selected_at: datetime | None = None