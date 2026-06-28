import logging
from pathlib import Path

from app.models import Outline, Research, Topic
from app.services.gemini import gemini_service

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class OutlineAgent:
    def __init__(self):
        self.prompt_template = load_prompt("outline.md")

    async def run(self, topic: Topic, research: Research) -> Outline:
        logger.info("Creating outline", topic=topic.title)

        research_json = research.model_dump_json(indent=2)
        prompt = (
            self.prompt_template
            .replace("{{topic.title}}", topic.title)
            .replace("{{research}}", research_json)
        )

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=Outline,
            temperature=0.5,
        )

        logger.info("Outline created", topic=topic.title, sections=len(result.sections))
        return result


async def create_outline(topic: Topic, research: Research) -> Outline:
    agent = OutlineAgent()
    return await agent.run(topic, research)