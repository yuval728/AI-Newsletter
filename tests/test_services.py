import os
import tempfile
from pathlib import Path

import pytest


class TestDatabase:
    @pytest.mark.asyncio
    async def test_database_initialization(self):
        from app.services.database import Database

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            db = Database(Path(db_path))
            await db.init()

            # Test basic operations
            topic_id = await db.create_topic("Test Topic", "Test reason", 85.0)
            assert topic_id > 0

            topic = await db.get_topic(topic_id)
            assert topic is not None
            assert topic.title == "Test Topic"
            assert topic.score == 85.0

            # Test affiliate links
            await db.create_affiliate_link("Test Tool", "http://test.com", "IDE")
            link = await db.get_affiliate_link("Test Tool")
            assert link is not None
            assert link.tool_name == "Test Tool"
        finally:
            os.unlink(db_path)


class TestMarkdownService:
    @pytest.mark.asyncio
    async def test_markdown_to_html(self):
        from app.services.markdown import markdown_service

        markdown = "# Heading\n\n**Bold** text\n\n- Item 1\n- Item 2"
        html = markdown_service.to_html(markdown)

        assert "<h1>Heading</h1>" in html
        assert "<strong>Bold</strong>" in html
        assert "<li>Item 1</li>" in html

    @pytest.mark.asyncio
    async def test_excerpt_extraction(self):
        from app.services.markdown import markdown_service

        markdown = "# Heading\n\nThis is a test excerpt that should be extracted."
        excerpt = markdown_service.extract_excerpt(markdown, max_length=50)

        assert len(excerpt) <= 53
        assert "test excerpt" in excerpt.lower()

    @pytest.mark.asyncio
    async def test_slug_generation(self):
        from app.services.markdown import markdown_service

        slug = markdown_service.generate_slug("Test Article: AI News & Updates!")
        assert slug == "test-article-ai-news-updates"


class TestHTMLService:
    @pytest.mark.asyncio
    async def test_html_rendering(self):
        from app.services.html import html_service

        html = html_service.render_article(
            title="Test Article",
            content="<p>Test content</p>",
            excerpt="Test excerpt"
        )

        assert "Test Article" in html
        assert "Test content" in html
        assert "Test excerpt" in html


class TestGeminiService:
    @pytest.mark.asyncio
    async def test_gemini_service_import(self):
        from app.services.gemini import gemini_service
        assert gemini_service is not None


class TestBeehiivService:
    @pytest.mark.asyncio
    async def test_beehiiv_service_import(self):
        from app.services.beehiiv import beehiiv_service
        assert beehiiv_service is not None


class TestImageService:
    @pytest.mark.asyncio
    async def test_image_service_import(self):
        from app.services.image import image_service
        assert image_service is not None
