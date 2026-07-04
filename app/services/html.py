from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings


class HTMLService:
    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_article(
        self,
        title: str,
        content: str,
        excerpt: str | None = None,
        author_name: str | None = None,
        publish_date: datetime | None = None,
        newsletter_name: str | None = None,
        featured_image: str | None = None,
    ) -> str:
        template = self.env.get_template("beehiiv.html.j2")
        return template.render(
            title=title,
            content=content,
            excerpt=excerpt,
            author_name=author_name or settings.newsletter_from_name,
            publish_date=publish_date or datetime.now(),
            newsletter_name=newsletter_name or settings.newsletter_name,
            featured_image=featured_image,
        )

    def render_simple(self, title: str, content: str) -> str:
        return self.render_article(title=title, content=content)


html_service = HTMLService()
