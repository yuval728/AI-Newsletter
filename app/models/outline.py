from pydantic import BaseModel


class OutlineSection(BaseModel):
    heading: str
    content_points: list[str] = []
    estimated_words: int = 200


class Outline(BaseModel):
    title: str
    introduction: OutlineSection
    sections: list[OutlineSection] = []
    conclusion: OutlineSection
    cta: str
