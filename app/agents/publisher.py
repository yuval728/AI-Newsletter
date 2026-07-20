from loguru import logger

from app.models import PublishResult
from app.services.beehiiv import beehiiv_service
from app.services.database import get_database
from app.services.html import html_service
from app.services.markdown import markdown_service


class PublisherAgent:
    def __init__(self):
        self.db = get_database()

    async def run(self, input_data=None) -> PublishResult:
        topic = input_data.get("topic")
        previous_result = input_data.get("previous_result")
        image = input_data.get("image")
        logger.info("Publishing to Beehiiv", title=topic.title)

        # Convert markdown to HTML
        html_content = markdown_service.to_html(previous_result.markdown)

        # Render full HTML email
        featured_image_path = image.file_path if image else None
        final_html = html_service.render_article(
            title=topic.title,
            content=html_content,
            excerpt=previous_result.excerpt,
            featured_image=featured_image_path,
        )

        # Create draft
        draft = await beehiiv_service.create_draft(
            title=topic.title,
            content=final_html,
            subtitle=previous_result.excerpt,
        )

        # Publish immediately
        post = await beehiiv_service.publish_post(draft.id)

        result = PublishResult(
            post_id=post.id,
            web_url=post.web_url,
            status=post.status,
        )

        logger.info("Published to Beehiiv", post_id=result.post_id, status=result.status)
        return result


async def publish_article(input_data=None) -> PublishResult:
    agent = PublisherAgent()
    return await agent.run(input_data)
