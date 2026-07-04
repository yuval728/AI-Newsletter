from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.models.affiliate import AffiliateResult
    from app.models.article import ArticleDraft
    from app.models.image import ImageAsset
    from app.models.outline import Outline
    from app.models.publish import PublishResult
    from app.models.research import Research
    from app.models.seo import SEOData
    from app.models.topic import Topic


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
