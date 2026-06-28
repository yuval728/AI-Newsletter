import logging
import time
from contextlib import asynccontextmanager

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.agents import (
    discover_topics,
    rank_topics,
    research_topic,
    create_outline,
    write_article,
    edit_article,
    generate_seo,
    insert_affiliate_links,
    generate_image,
    publish_article,
)
from app.models import (
    TopicCandidate,
    Topic,
    Research,
    ArticleDraft,
    SEOData,
    AffiliateResult,
    ImageAsset,
    PublishResult,
)
from app.services.database import get_database

logger = logging.getLogger(__name__)


class PipelineStage:
    def __init__(self, name: str, func, **kwargs):
        self.name = name
        self.func = func
        self.kwargs = kwargs

    async def run(self, input_data=None):
        stage_logger = logging.getLogger(f"{__name__}.PipelineStage.{self.name}")
        try:
            stage_logger.info(f"Starting {self.name}")
            result = await self.func(input_data, **self.kwargs)
            stage_logger.info(f"Completed {self.name}")
            return result
        except Exception as e:
            stage_logger.error(f"Failed {self.name}: {str(e)}", exc_info=True)
            raise


class NewsletterPipeline:
    def __init__(self):
        self.db = get_database()
        self.run_id: int | None = None
        self.current_stage: str = ""
        
        self.stages = [
            PipelineStage("topic_discovery", discover_topics),
            PipelineStage("topic_ranking", rank_topics, lambda data: rank_topics(data)),
            PipelineStage("research", research_topic, lambda data: research_topic(data)),
            PipelineStage("outline", create_outline, lambda data: create_outline(data["topic"], data["research"])),
            PipelineStage("writing", write_article, lambda data: write_article(data["topic"], data["outline"], data["research"])),
            PipelineStage("editing", edit_article, lambda data: edit_article(data["previous_result"])),
            PipelineStage("seo", generate_seo, lambda data: generate_seo(data["previous_result"], data["topic"])),
            PipelineStage("affiliate", insert_affiliate_links, lambda data: insert_affiliate_links(data["previous_result"])),
            PipelineStage("image", generate_image, lambda data: generate_image(data["topic"].title, data["previous_result"].excerpt)),
            PipelineStage("publishing", publish_article, lambda data: publish_article(
                data["topic"].title,
                data["previous_result"].markdown,
                data["previous_result"].excerpt,
                data["seo"].slug,
                data["image"].file_path if data["image"] else None,
                settings.auto_publish
            )),
        ]

    async def save_run_start(self):
        self.run_id = await self.db.create_run()
        logger.info("Pipeline run started", run_id=self.run_id)

    async def save_stage_result(self, stage_name: str, result, tokens_used: int = 0, cost_usd: float = 0.0):
        if not self.run_id:
            return

        await self.db.update_run(
            run_id=self.run_id,
            status="running",
            runtime_seconds=None,
            error_message=None,
            error_stage=None,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            article_id=None,
        )
        logger.info(f"Saved result for stage: {stage_name}", stage=stage_name)

    @retry(
        wait=wait_exponential(multiplier=settings.retry_backoff, min=2, max=30),
        stop=stop_after_attempt(settings.max_retries),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def run_stage(self, stage: PipelineStage, input_data=None):
        try:
            self.current_stage = stage.name
            logger.info(f"Stage {stage.name} start", input_data=input_data)
            result = await stage.run(input_data)
            logger.info(f"Stage {stage.name} completed")

            # Extract tokens and cost for logging (priority)
            tokens_used = 0
            cost_usd = 0.0
            if hasattr(result, "tokens_used"):
                tokens_used = result.tokens_used
            if hasattr(result, "cost_usd"):
                cost_usd = result.cost_usd

            await self.save_stage_result(stage.name, result, tokens_used, cost_usd)
            logger.info(f"Stage {stage.name} result saved", tokens_used=tokens_used, cost_usd=cost_usd)
            return result

        except Exception as e:
            logger.error(f"Stage {stage.name} failed", error=str(e), stage=stage.name)
            raise

    async def run(self) -> dict:
        stage_logger = logging.getLogger(f"{__name__}.Pipeline.run")
        stage_logger.info("Starting newsletter pipeline")

        await self.save_run_start()

        try:
            # Stage 1: Topic Discovery
            candidates = await self.run_stage(self.stages[0])

            # Stage 2: Topic Ranking
            topic = await self.run_stage(self.stages[1], candidates)

            # Stage 3: Research
            research = await self.run_stage(self.stages[2], topic)

            # Stage 4: Outline
            outline = await self.run_stage(self.stages[3], {"topic": topic, "research": research})

            # Stage 5: Writing
            draft = await self.run_stage(self.stages[4], {"topic": topic, "outline": outline, "research": research})

            # Stage 6: Editing
            edited_draft = await self.run_stage(self.stages[5], {"previous_result": draft})

            # Stage 7: SEO
            seo = await self.run_stage(self.stages[6], {"previous_result": edited_draft, "topic": topic})

            # Stage 8: Affiliate Links
            affiliate_result = await self.run_stage(self.stages[7], {"previous_result": seo})

            # Stage 9: Image Generation
            image = await self.run_stage(self.stages[8], {"topic": topic, "previous_result": affiliate_result})

            # Stage 10: Publishing
            publish_result = await self.run_stage(self.stages[9], {
                "topic": topic,
                "previous_result": affiliate_result,
                "seo": seo,
                "image": image,
            })

            # Update run status to completed
            if self.run_id:
                await self.db.update_run(
                    run_id=self.run_id,
                    status="completed",
                    runtime_seconds=None,
                    error_message=None,
                    error_stage=None,
                    tokens_used=0,
                    cost_usd=0.0,
                    article_id=None,
                )

            stage_logger.info("Pipeline completed successfully")
            return {
                "run_id": self.run_id,
                "topic": topic.model_dump(),
                "draft": draft.model_dump(),
                "seo": seo.model_dump(),
                "affiliate_result": affiliate_result.model_dump(),
                "image": image.model_dump() if image else None,
                "publish_result": publish_result.model_dump(),
            }

        except Exception as e:
            logger.error(f"Pipeline failed at stage {self.current_stage}", error=str(e))
            if self.run_id:
                await self.db.update_run(
                    run_id=self.run_id,
                    status="failed",
                    runtime_seconds=None,
                    error_message=str(e),
                    error_stage=self.current_stage,
                    tokens_used=0,
                    cost_usd=0.0,
                    article_id=None,
                )
            raise


async def run_full_pipeline() -> dict:
    pipeline = NewsletterPipeline()
    return await pipeline.run()