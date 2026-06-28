import logging
from pathlib import Path

from app.models import ArticleDraft, SEOData, Topic
from app.services.gemini import gemini_service

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class SEOAgent:
    def __init__(self):
        self.prompt_template = load_prompt("seo.md")

    async def run(self, draft: ArticleDraft, topic: Topic) -> SEOData:
        logger.info("Generating SEO data", title=draft.title)

        prompt = (
            self.prompt_template
            .replace("{{draft.markdown}}", draft.markdown)
            .replace("{{topic.title}}", topic.title)
        )

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=SEOData,
            temperature=0.3,
        )

        logger.info("SEO data generated", slug=result.slug, keywords=result.keywords)
        return result


async def generate_seo(draft: ArticleDraft, topic: Topic) -> SEOData:
    agent = SEOAgent()
    return await agent.run(draft, topic)