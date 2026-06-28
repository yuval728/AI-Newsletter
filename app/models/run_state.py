from typing import Any
from pydantic import BaseModel
from app.models import Topic, Research, Outline, ArticleDraft, SEOData, AffiliateResult, ImageAsset, PublishResult


class RunState(BaseModel):
    run_id: int
    status: str = "running"
    current_stage: str = ""
    topic: Topic | None = None
    research: Research | None = None
    outline: Outline | None = None
    draft: ArticleDraft | None = None
    edited_draft: ArticleDraft | None = None
    seo: SEOData | None = None
    affiliate_result: AffiliateResult | None = None
    image: ImageAsset | None = None
    final_html: str | None = None
    publish_result: PublishResult | None = None
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0