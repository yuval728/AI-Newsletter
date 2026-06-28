from pydantic import BaseModel, Field


class SEOData(BaseModel):
    meta_description: str = Field(..., max_length=160)
    slug: str
    keywords: list[str] = []
    tags: list[str] = []