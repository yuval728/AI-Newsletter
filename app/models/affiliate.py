from pydantic import BaseModel


class AffiliateMatch(BaseModel):
    tool_name: str
    affiliate_url: str
    context: str


class AffiliateResult(BaseModel):
    matches: list[AffiliateMatch] = []
    modified_markdown: str
