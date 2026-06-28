import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import TopicCandidate, Topic, Research, ArticleDraft, SEOData


class TestModels:
    def test_topic_candidate(self):
        candidate = TopicCandidate(
            title="Test Topic",
            reason="Test reason",
            score=85.0
        )
        assert candidate.title == "Test Topic"
        assert candidate.score == 85.0

    def test_topic(self):
        topic = Topic(
            title="Test Topic",
            reason="Test reason",
            score=90.0
        )
        assert topic.title == "Test Topic"
        assert topic.score == 90.0

    def test_research(self):
        research = Research(
            facts=[],
            sources=[],
            quotes=[]
        )
        assert len(research.facts) == 0

    def test_article_draft(self):
        draft = ArticleDraft(
            title="Test Article",
            excerpt="Test excerpt",
            markdown="# Test\n\nContent here"
        )
        assert draft.title == "Test Article"
        assert draft.word_count == 0  # Not auto-calculated

    def test_seo_data(self):
        seo = SEOData(
            meta_description="Test description",
            slug="test-slug",
            keywords=["keyword1", "keyword2"],
            tags=["tag1"]
        )
        assert seo.slug == "test-slug"
        assert len(seo.keywords) == 2


class TestConfig:
    def test_settings_load(self):
        from app.config import settings
        # Should not raise even without .env
        assert settings is not None


@pytest.mark.asyncio
async def test_pipeline_import():
    from app.pipeline import run_full_pipeline
    assert run_full_pipeline is not None