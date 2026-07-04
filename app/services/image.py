import hashlib
from typing import Any
from urllib.parse import quote_plus

import httpx
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings


class ImageService:
    def __init__(self):
        self.base_url = settings.pollinations_base_url
        self.client = httpx.AsyncClient(timeout=settings.request_timeout)
        settings.assets_images_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, prompt: str, extension: str = "png") -> str:
        hash_obj = hashlib.md5(prompt.encode()).hexdigest()[:12]
        return f"newsletter_{hash_obj}.{extension}"

    def _build_prompt(self, title: str, summary: str, style: str = "minimal") -> str:
        style_prompts = {
            "minimal": (
                "Clean minimal flat illustration for AI newsletter. "
                "Style: simple geometric shapes, thin lines, 2-3 color palette (indigo/white/gray), "
                "tech symbols (neural nodes, code brackets, data flow), white background, "
                "vector art, professional, no text, 16:9 aspect ratio"
            ),
            "abstract": (
                "Abstract AI/neural network visualization. "
                "Gradient blobs, interconnected nodes, futuristic, ethereal glow, "
                "deep blues and purples, 16:9 aspect ratio"
            ),
            "code": (
                "Code/terminal aesthetic illustration. "
                "Monospace font, syntax highlighting colors, code brackets, "
                "terminal window, dark background with green/amber text, 16:9 aspect ratio"
            ),
        }
        base_style = style_prompts.get(style, style_prompts["minimal"])
        return f"{base_style}. Topic: {title}. Summary: {summary}"

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def generate_image(
        self,
        title: str,
        summary: str,
        style: str = "minimal",
        width: int | None = None,
        height: int | None = None,
    ) -> dict[str, Any]:
        prompt = self._build_prompt(title, summary, style)
        encoded_prompt = quote_plus(prompt)

        width = width or settings.image_width
        height = height or settings.image_height

        url = f"{self.base_url}/{encoded_prompt}?width={width}&height={height}&model={settings.image_model}&nologo=true&private=true"

        response = await self.client.get(url)
        response.raise_for_status()

        filename = self._generate_filename(prompt)
        file_path = settings.assets_images_dir / filename

        with open(file_path, "wb") as f:
            f.write(response.content)

        logger.info("Image generated", file_path=str(file_path), size=len(response.content))

        return {
            "file_path": str(file_path),
            "filename": filename,
            "prompt": prompt,
            "width": width,
            "height": height,
            "size_bytes": len(response.content),
        }

    async def generate_image_from_prompt(
        self,
        prompt: str,
        width: int | None = None,
        height: int | None = None,
    ) -> dict[str, Any]:
        encoded_prompt = quote_plus(prompt)

        width = width or settings.image_width
        height = height or settings.image_height

        url = f"{self.base_url}/{encoded_prompt}?width={width}&height={height}&model={settings.image_model}&nologo=true&private=true"

        response = await self.client.get(url)
        response.raise_for_status()

        filename = self._generate_filename(prompt)
        file_path = settings.assets_images_dir / filename

        with open(file_path, "wb") as f:
            f.write(response.content)

        return {
            "file_path": str(file_path),
            "filename": filename,
            "prompt": prompt,
            "width": width,
            "height": height,
            "size_bytes": len(response.content),
        }

    async def close(self):
        await self.client.aclose()


image_service = ImageService()
