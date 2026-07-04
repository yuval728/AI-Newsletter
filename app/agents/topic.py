import logging

from app.models import Topic, TopicCandidate
from app.prompts import load_prompt
from app.services.database import get_database
from app.services.gemini import gemini_service

logger = logging.getLogger(__name__)


class TopicDiscoveryAgent:
    def __init__(self):
        self.db = get_database()

    async def run(self, input_data=None) -> list[TopicCandidate]:
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

    async def run(self, input_data=None) -> Topic:
        candidates = input_data if isinstance(input_data, list) else []
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


async def discover_topics(input_data=None) -> list[TopicCandidate]:
    agent = TopicDiscoveryAgent()
    return await agent.run(input_data)


async def rank_topics(input_data=None) -> Topic:
    agent = TopicRankingAgent()
    return await agent.run(input_data)
