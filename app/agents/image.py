from pathlib import Path

from loguru import logger

from app.models import ImageAsset
from app.services.gemini import gemini_service
from app.services.image import image_service


def load_prompt(name: str) -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


class ImageAgent:
    def __init__(self):
        self.prompt_template = load_prompt("image.md")

    async def run(self, input_data=None) -> ImageAsset:
        """Generate only the hero/featured image for the newsletter header."""
        topic = input_data.get("topic")
        previous_result = input_data.get("previous_result")
        logger.info("Generating hero image", title=topic.title)

        prompt = (
            self.prompt_template
            .replace("{{title}}", topic.title)
            .replace("{{summary}}", previous_result.excerpt)
        )

        # Use Gemini to refine the prompt
        refined_prompt = await gemini_service.generate_text(
            prompt=prompt,
            temperature=0.3,
        )

        # Generate hero image via Pollinations
        result = await image_service.generate_image_from_prompt(refined_prompt)

        asset = ImageAsset(
            file_path=result["file_path"],
            prompt=refined_prompt,
            width=result["width"],
            height=result["height"],
            size_bytes=result["size_bytes"],
        )

        logger.info("Hero image generated", file_path=asset.file_path)
        return asset


async def generate_image(input_data=None) -> ImageAsset:
    agent = ImageAgent()
    return await agent.run(input_data)
