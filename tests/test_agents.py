
import pytest


@pytest.mark.asyncio
async def test_topic_discovery_agent_import():
    from app.agents.topic import TopicDiscoveryAgent
    assert TopicDiscoveryAgent is not None


@pytest.mark.asyncio
async def test_research_agent_import():
    from app.agents.research import ResearchAgent
    assert ResearchAgent is not None


@pytest.mark.asyncio
async def test_outline_agent_import():
    from app.agents.outline import OutlineAgent
    assert OutlineAgent is not None


@pytest.mark.asyncio
async def test_writer_agent_import():
    from app.agents.writer import WriterAgent
    assert WriterAgent is not None


@pytest.mark.asyncio
async def test_editor_agent_import():
    from app.agents.editor import EditorAgent
    assert EditorAgent is not None


@pytest.mark.asyncio
async def test_seo_agent_import():
    from app.agents.seo import SEOAgent
    assert SEOAgent is not None


@pytest.mark.asyncio
async def test_affiliate_agent_import():
    from app.agents.affiliate import AffiliateAgent
    assert AffiliateAgent is not None


@pytest.mark.asyncio
async def test_image_agent_import():
    from app.agents.image import ImageAgent
    assert ImageAgent is not None


@pytest.mark.asyncio
async def test_publisher_agent_import():
    from app.agents.publisher import PublisherAgent
    assert PublisherAgent is not None
