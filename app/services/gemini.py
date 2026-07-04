import json
from typing import TypeVar

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        self.search_model = genai.GenerativeModel(settings.gemini_search_model)

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        temperature: float | None = None,
        use_search: bool = False,
    ) -> T:
        config = GenerationConfig(
            temperature=temperature or settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
            response_mime_type="application/json",
            response_schema=response_model,
        )

        tools: list[Tool] = []
        if use_search:
            tools = [Tool(google_search={})]

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        try:
            if use_search:
                response = await self.search_model.generate_content_async(
                    full_prompt,
                    generation_config=config,
                    tools=tools,
                )
            else:
                response = await self.model.generate_content_async(
                    full_prompt,
                    generation_config=config,
                )

            if not response.text:
                raise ValueError("Empty response from Gemini")

            data = json.loads(response.text)
            return response_model.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=response.text[:500] if response.text else "empty")
            raise ValueError(f"Invalid JSON from Gemini: {e}")
        except Exception as e:
            logger.error("Gemini generation failed", error=str(e), prompt=prompt[:200])
            raise

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
        use_search: bool = False,
    ) -> str:
        config = GenerationConfig(
            temperature=temperature or settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_tokens,
        )

        tools: list[Tool] = []
        if use_search:
            tools = [Tool(google_search={})]

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        try:
            if use_search:
                response = await self.search_model.generate_content_async(
                    full_prompt,
                    generation_config=config,
                    tools=tools,
                )
            else:
                response = await self.model.generate_content_async(
                    full_prompt,
                    generation_config=config,
                )

            if not response.text:
                raise ValueError("Empty response from Gemini")

            return response.text.strip()

        except Exception as e:
            logger.error("Gemini text generation failed", error=str(e), prompt=prompt[:200])
            raise


gemini_service = GeminiService()
