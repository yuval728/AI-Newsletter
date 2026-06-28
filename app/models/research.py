from pydantic import BaseModel


class ResearchSource(BaseModel):
    title: str
    url: str
    snippet: str | None = None


class ResearchFact(BaseModel):
    fact: str
    source: str


class ResearchQuote(BaseModel):
    quote: str
    author: str
    source: str


class Research(BaseModel):
    facts: list[ResearchFact] = []
    sources: list[ResearchSource] = []
    quotes: list[ResearchQuote] = []