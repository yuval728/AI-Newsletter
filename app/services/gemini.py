import json
from typing import TypeVar

from google import genai
from google.genai import types
from loguru import logger
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

T = TypeVar("T", bound=BaseModel)


def _is_not_rate_limit(exception: BaseException) -> bool:
    error_str = str(exception).lower()
    return "429" not in error_str and "resource_exhausted" not in error_str


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.gemini_model
        self.search_model = settings.gemini_search_model

    @retry(
        wait=wait_exponential(multiplier=10, min=10, max=120),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_not_rate_limit),
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
        temp = temperature or settings.gemini_temperature
        contents = prompt
        if system_instruction:
            contents = f"{system_instruction}\n\n{prompt}"

        model = self.search_model if use_search else self.model

        if use_search:
            config = types.GenerateContentConfig(
                temperature=temp,
                max_output_tokens=settings.gemini_max_tokens,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
            try:
                response = await self.client.aio.models.generate_content(
                    model=model, contents=contents, config=config,
                )
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                data = json.loads(response.text)
                return response_model.model_validate(data)
            except json.JSONDecodeError:
                logger.warning("Search response not JSON, retrying without search")
                return await self._generate_structured_no_search(
                    contents, response_model, temp
                )
        else:
            return await self._generate_structured_no_search(
                contents, response_model, temp
            )

    async def _generate_structured_no_search(
        self, contents: str, response_model: type[T], temperature: float
    ) -> T:
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=settings.gemini_max_tokens,
            response_mime_type="application/json",
            response_schema=response_model,
        )
        response = await self.client.aio.models.generate_content(
            model=self.model, contents=contents, config=config,
        )
        if not response.text:
            raise ValueError("Empty response from Gemini")
        data = json.loads(response.text)
        return response_model.model_validate(data)

    @retry(
        wait=wait_exponential(multiplier=10, min=10, max=120),
        stop=stop_after_attempt(5),
        retry=retry_if_exception(_is_not_rate_limit),
        reraise=True,
    )
    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
        use_search: bool = False,
    ) -> str:
        temp = temperature or settings.gemini_temperature
        contents = prompt
        if system_instruction:
            contents = f"{system_instruction}\n\n{prompt}"

        model = self.search_model if use_search else self.model

        kwargs: dict = {"temperature": temp, "max_output_tokens": settings.gemini_max_tokens}
        if use_search:
            kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
        config = types.GenerateContentConfig(**kwargs)

        response = await self.client.aio.models.generate_content(
            model=model, contents=contents, config=config,
        )

        if not response.text:
            raise ValueError("Empty response from Gemini")

        return response.text.strip()


gemini_service = GeminiService()
