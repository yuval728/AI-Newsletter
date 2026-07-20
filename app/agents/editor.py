from pathlib import Path

from loguru import logger

from app.models import ArticleDraft
from app.services.gemini import gemini_service


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class EditorAgent:
    def __init__(self):
        self.prompt_template = load_prompt("editor.md")

    async def run(self, input_data=None) -> ArticleDraft:
        draft = input_data.get("previous_result")
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


async def edit_article(input_data=None) -> ArticleDraft:
    agent = EditorAgent()
    return await agent.run(input_data)
