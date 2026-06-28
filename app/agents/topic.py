import logging
from typing import Any

from app.models import TopicCandidate, Topic
from app.prompts import load_prompt
from app.services.gemini import gemini_service
from app.services.database import get_database

logger = logging.getLogger(__name__)


class TopicDiscoveryAgent:
    def __init__(self):
        self.db = get_database()

    async def run(self) -> list[TopicCandidate]:
        logger.info("Starting topic discovery")
        prompt = load_prompt("topic_discovery.md")

        result = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=list[TopicCandidate],
            use_search=True,
            temperature=0.8,
        )

        for candidate in result:
            await self.db.create_topic(
                title=candidate.title,
                reason=candidate.reason,
                score=candidate.score,
            )

        logger.info("Topic discovery complete", count=len(result))
        return result


class TopicRankingAgent:
    def __init__(self):
        self.db = get_database()

    async def run(self, candidates: list[TopicCandidate]) -> Topic:
        logger.info("Starting topic ranking", candidate_count=len(candidates))
        prompt = load_prompt("topic_ranking.md")

        candidates_json = "\n".join(
            [f"- {c.title}: {c.reason} (score: {c.score})" for c in candidates]
        )
        full_prompt = f"{prompt}\n\nCandidates:\n{candidates_json}"

        result = await gemini_service.generate_structured(
            prompt=full_prompt,
            response_model=Topic,
            temperature=0.3,
        )

        await self.db.mark_topic_selected(result.title)
        logger.info("Topic selected", title=result.title, score=result.score)
        return result


async def discover_topics() -> list[TopicCandidate]:
    agent = TopicDiscoveryAgent()
    return await agent.run()


async def rank_topics(candidates: list[TopicCandidate]) -> Topic:
    agent = TopicRankingAgent()
    return await agent.run(candidates)