import logging
from datetime import datetime

from app.models import PublishResult
from app.services.beehiiv import beehiiv_service
from app.services.database import get_database
from app.services.html import html_service
from app.services.markdown import markdown_service

logger = logging.getLogger(__name__)


class PublisherAgent:
    def __init__(self):
        self.db = get_database()

    async def run(
        self,
        title: str,
        markdown: str,
        excerpt: str,
        slug: str,
        featured_image_path: str | None = None,
        auto_publish: bool = True,
    ) -> PublishResult:
        logger.info("Publishing to Beehiiv", title=title)

        # Convert markdown to HTML
        html_content = markdown_service.to_html(markdown)

        # Render full HTML email
        final_html = html_service.render_article(
            title=title,
            content=html_content,
            excerpt=excerpt,
            featured_image=featured_image_path,
        )

        if auto_publish:
            # Create draft
            draft = await beehiiv_service.create_draft(
                title=title,
                content=final_html,
                subtitle=excerpt,
            )

            # Publish immediately
            post = await beehiiv_service.publish_post(draft.id)

            result = PublishResult(
                post_id=post.id,
                web_url=post.web_url,
                status=post.status,
            )
        else:
            # Just create draft
            draft = await beehiiv_service.create_draft(
                title=title,
                content=final_html,
                subtitle=excerpt,
            )
            result = PublishResult(
                post_id=draft.id,
                web_url="",
                status="draft",
            )

        logger.info("Published to Beehiiv", post_id=result.post_id, status=result.status)
        return result


async def publish_article(
    title: str,
    markdown: str,
    excerpt: str,
    slug: str,
    featured_image_path: str | None = None,
    auto_publish: bool = True,
) -> PublishResult:
    agent = PublisherAgent()
    return await agent.run(
        title=title,
        markdown=markdown,
        excerpt=excerpt,
        slug=slug,
        featured_image_path=featured_image_path,
        auto_publish=auto_publish,
    )