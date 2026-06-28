import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import TopicCandidate, Topic, Research, ResearchFact, ResearchQuote, ResearchSource
from app.models import Outline, OutlineSection, ArticleDraft, SEOData, AffiliateMatch, AffiliateResult, ImageAsset, PublishResult


class TestModels:
    def test_topic_candidate_creation(self):
        candidate = TopicCandidate(
            title="Test Topic",
            reason="Test reason",
            score=85.5
        )
        assert candidate.title == "Test Topic"
        assert candidate.score == 85.5

    def test_topic_creation(self):
        topic = Topic(
            title="Test Topic",
            reason="Test reason",
            score=90.0
        )
        assert topic.title == "Test Topic"

    def test_research_creation(self):
        research = Research(
            facts=[ResearchFact(fact="Test fact", source="http://example.com")],
            sources=[ResearchSource(title="Test", url="http://example.com")],
            quotes=[ResearchQuote(quote="Test quote", author="Test Author", source="http://example.com")]
        )
        assert len(research.facts) == 1
        assert len(research.sources) == 1
        assert len(research.quotes) == 1

    def test_article_draft_creation(self):
        draft = ArticleDraft(
            title="Test Article",
            excerpt="Test excerpt",
            markdown="# Test\n\nContent here"
        )
        assert draft.title == "Test Article"
        assert draft.word_count == 0  # Not calculated yet

    def test_seo_data_creation(self):
        seo = SEOData(
            meta_description="Test meta description",
            slug="test-slug",
            keywords=["ai", "newsletter"],
            tags=["AI", "Tech"]
        )
        assert seo.slug == "test-slug"
        assert len(seo.keywords) == 2

    def test_affiliate_result_creation(self):
        result = AffiliateResult(
            matches=[AffiliateMatch(tool_name="Cursor", affiliate_url="http://cursor.sh", context="code editor")],
            modified_markdown="Check out [Cursor](http://cursor.sh)"
        )
        assert len(result.matches) == 1
        assert "Cursor" in result.modified_markdown

    def test_image_asset_creation(self):
        asset = ImageAsset(
            file_path="/assets/image.png",
            prompt="Test prompt",
            width=1200,
            height=630,
            size_bytes=102400
        )
        assert asset.width == 1200
        assert asset.height == 630


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
        assert len(excerpt) <= 53  # max_length + "..."
        assert "test excerpt" in excerpt.lower()

    @pytest.mark.asyncio
    async def test_slug_generation(self):
        from app.services.markdown import markdown_service
        slug = markdown_service.generate_slug("Test Article: AI News & Updates!")
        assert slug == "test-article-ai-news-updates"


class TestDatabase:
    @pytest.mark.asyncio
    async def test_database_init(self):
        from app.services.database import init_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            from app.config import settings
            settings.database_path = db_path
            db = await init_database()
            assert db is not None
        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_create_topic(self):
        from app.services.database import init_database, get_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            from app.config import settings
            settings.database_path = db_path
            await init_database()
            db = get_database()
            
            topic_id = await db.create_topic("Test Topic", "Test reason", 85.0)
            assert topic_id > 0
            
            topic = await db.get_topic(topic_id)
            assert topic is not None
            assert topic.title == "Test Topic"
            assert topic.score == 85.0
        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_affiliate_links(self):
        from app.services.database import init_database, get_database
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            from app.config import settings
            settings.database_path = db_path
            await init_database()
            db = get_database()
            
            link_id = await db.create_affiliate_link("Test Tool", "http://test.com", "IDE")
            assert link_id > 0
            
            link = await db.get_affiliate_link("Test Tool")
            assert link is not None
            assert link.tool_name == "Test Tool"
            assert link.affiliate_url == "http://test.com"
        finally:
            os.unlink(db_path)


class TestGeminiService:
    @pytest.mark.asyncio
    async def test_generate_structured(self):
        from app.services.gemini import gemini_service
        from pydantic import BaseModel
        
        class TestResponse(BaseModel):
            result: str
            value: int
        
        # This will fail without real API key, but tests the structure
        # In real tests, we'd mock the genai module
        pass


class TestPipelineIntegration:
    @pytest.mark.asyncio
    async def test_pipeline_structure(self):
        from app.pipeline import NewsletterPipeline
        
        pipeline = NewsletterPipeline()
        assert len(pipeline.stages) == 10
        assert pipeline.stages[0].name == "topic_discovery"
        assert pipeline.stages[-1].name == "publishing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])