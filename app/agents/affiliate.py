import logging
from pathlib import Path

from app.models import AffiliateResult, ArticleDraft
from app.services.gemini import gemini_service
from app.services.database import get_database

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class AffiliateAgent:
    def __init__(self):
        self.prompt_template = load_prompt("affiliate.md")
        self.db = get_database()

    async def run(self, draft: ArticleDraft) -> AffiliateResult:
        logger.info("Inserting affiliate links", title=draft.title)

        affiliate_links = await self.db.get_affiliate_links()
        tools_text = "\n".join(
            [f"- {link.tool_name}: {link.affiliate_url} ({link.category})" for link in affiliate_links]
        )

        prompt = (
            self.prompt_template
            .replace("{{draft.markdown}}", draft.markdown)
            .replace("{{affiliate_tools}}", tools_text)
        )

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=AffiliateResult,
            temperature=0.2,
        )

        logger.info("Affiliate links inserted", title=draft.title, matches=len(result.matches))
        return result


async def insert_affiliate_links(draft: ArticleDraft) -> AffiliateResult:
    agent = AffiliateAgent()
    return await agent.run(draft)