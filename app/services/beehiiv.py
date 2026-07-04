from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings


@dataclass
class BeehiivDraft:
    id: str
    title: str
    content: str
    status: str
    web_url: str | None = None


@dataclass
class BeehiivPost:
    id: str
    title: str
    status: str
    web_url: str
    publish_url: str | None = None


class BeehiivService:
    def __init__(self):
        self.base_url = settings.beehiiv_base_url
        self.headers = {
            "Authorization": f"Bearer {settings.beehiiv_api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=settings.request_timeout,
        )

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def create_draft(
        self,
        title: str,
        content: str,
        subtitle: str | None = None,
        tags: list[str] | None = None,
    ) -> BeehiivDraft:
        url = f"/publications/{settings.publication_id}/posts"

        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "status": "draft",
        }
        if subtitle:
            payload["subtitle"] = subtitle
        if tags:
            payload["tags"] = tags

        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        post_data = data.get("data", {})
        return BeehiivDraft(
            id=post_data.get("id", ""),
            title=post_data.get("title", title),
            content=post_data.get("content", content),
            status=post_data.get("status", "draft"),
        )

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def publish_post(self, post_id: str) -> BeehiivPost:
        url = f"/publications/{settings.publication_id}/posts/{post_id}/publish"

        response = await self.client.post(url, json={})
        response.raise_for_status()
        data = response.json()

        post_data = data.get("data", {})
        return BeehiivPost(
            id=post_data.get("id", post_id),
            title=post_data.get("title", ""),
            status=post_data.get("status", "published"),
            web_url=post_data.get("web_url", ""),
            publish_url=post_data.get("publish_url"),
        )

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def update_post(
        self,
        post_id: str,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
    ) -> BeehiivPost:
        url = f"/publications/{settings.publication_id}/posts/{post_id}"

        payload: dict[str, Any] = {}
        if title:
            payload["title"] = title
        if content:
            payload["content"] = content
        if status:
            payload["status"] = status

        response = await self.client.patch(url, json=payload)
        response.raise_for_status()
        data = response.json()

        post_data = data.get("data", {})
        return BeehiivPost(
            id=post_data.get("id", post_id),
            title=post_data.get("title", ""),
            status=post_data.get("status", "draft"),
            web_url=post_data.get("web_url", ""),
        )

    async def get_post(self, post_id: str) -> BeehiivPost | None:
        url = f"/publications/{settings.publication_id}/posts/{post_id}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            post_data = data.get("data", {})
            return BeehiivPost(
                id=post_data.get("id", post_id),
                title=post_data.get("title", ""),
                status=post_data.get("status", ""),
                web_url=post_data.get("web_url", ""),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def close(self):
        await self.client.aclose()


beehiiv_service = BeehiivService()
