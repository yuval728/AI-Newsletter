import logging
from pathlib import Path

from app.models import ArticleDraft, Outline, Research, Topic
from app.services.gemini import gemini_service

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class WriterAgent:
    def __init__(self):
        self.prompt_template = load_prompt("writer.md")

    async def run(self, topic: Topic, outline: Outline, research: Research) -> ArticleDraft:
        logger.info("Writing article", topic=topic.title)

        prompt = (
            self.prompt_template
            .replace("{{topic.title}}", topic.title)
            .replace("{{outline}}", outline.model_dump_json(indent=2))
            .replace("{{research}}", research.model_dump_json(indent=2))
        )

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=ArticleDraft,
            temperature=0.7,
        )

        result.word_count = len(result.markdown.split())
        logger.info("Article written", topic=topic.title, words=result.word_count)
        return result


async def write_article(topic: Topic, outline: Outline, research: Research) -> ArticleDraft:
    agent = WriterAgent()
    return await agent.run(topic, outline, research)