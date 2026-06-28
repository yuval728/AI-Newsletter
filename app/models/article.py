from pydantic import BaseModel


class ArticleDraft(BaseModel):
    title: str
    excerpt: str
    markdown: str
    word_count: int = 0