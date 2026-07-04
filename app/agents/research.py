import logging
from pathlib import Path

from app.models import Research
from app.services.gemini import gemini_service

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class ResearchAgent:
    def __init__(self):
        self.prompt_template = load_prompt("research.md")

    async def run(self, input_data=None) -> Research:
        topic = input_data
        logger.info("Starting research", topic=topic.title)

        prompt = self.prompt_template.replace("{{topic.title}}", topic.title).replace(
            "{{topic.reason}}", topic.reason or ""
        )

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=Research,
            use_search=True,
            temperature=0.4,
        )

        logger.info(
            "Research complete",
            topic=topic.title,
            facts=len(result.facts),
            sources=len(result.sources),
            quotes=len(result.quotes),
        )
        return result


async def research_topic(input_data=None) -> Research:
    agent = ResearchAgent()
    return await agent.run(input_data)
