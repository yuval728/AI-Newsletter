import logging
from pathlib import Path

from app.models import ArticleDraft
from app.services.gemini import gemini_service

logger = logging.getLogger(__name__)


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class EditorAgent:
    def __init__(self):
        self.prompt_template = load_prompt("editor.md")

    async def run(self, draft: ArticleDraft) -> ArticleDraft:
        logger.info("Editing article", title=draft.title)

        prompt = self.prompt_template.replace("{{draft.markdown}}", draft.markdown)

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=ArticleDraft,
            temperature=0.3,
        )

        result.word_count = len(result.markdown.split())
        logger.info("Editing complete", title=result.title, words=result.word_count)
        return result


async def edit_article(draft: ArticleDraft) -> ArticleDraft:
    agent = EditorAgent()
    return await agent.run(draft)