import argparse
import asyncio
import sys

from app.config import settings
from app.pipeline import run_full_pipeline
from app.services.database import init_database
from app.utils.logging import get_logger, setup_logging

logger = get_logger("main")


async def seed_affiliate_links():
    """Seed affiliate links from JSON file."""
    import json
    from pathlib import Path

    seed_file = Path("seeds/affiliate_links.json")
    if not seed_file.exists():
        logger.warning("Seed file not found", path=str(seed_file))
        return

    from app.services.database import get_database
    db = get_database()

    with open(seed_file) as f:
        links = json.load(f)

    count = await db.bulk_insert_affiliate_links(links)
    logger.info("Seeded affiliate links", count=count)


async def run_pipeline(dry_run: bool = False, topic: str | None = None):
    """Run the full newsletter pipeline."""
    logger.info("Starting newsletter pipeline", dry_run=dry_run, custom_topic=topic)

    # Initialize database
    await init_database()

    # Seed affiliate links on first run
    await seed_affiliate_links()

    # Override auto_publish if dry_run
    if dry_run:
        settings.auto_publish = False

    try:
        result = await run_full_pipeline()
        logger.info("Pipeline completed successfully", result=result)
        return result
    except Exception as e:
        logger.error("Pipeline failed", error=str(e), exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description="AI Newsletter Automation")
    parser.add_argument("--dry-run", action="store_true", help="Run without publishing to Beehiiv")
    parser.add_argument("--topic", type=str, help="Custom topic to write about")
    parser.add_argument("--seed", action="store_true", help="Only seed affiliate links")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level")

    args = parser.parse_args()

    # Override settings from CLI
    if args.log_level:
        settings.log_level = args.log_level.upper()

    # Setup logging
    setup_logging()

    if args.seed:
        asyncio.run(seed_affiliate_links())
        return

    try:
        result = asyncio.run(run_pipeline(dry_run=args.dry_run, topic=args.topic))
        print("\n✅ Pipeline completed successfully!")
        print(f"Run ID: {result.get('run_id')}")
        if result.get('publish_result'):
            print(f"Published: {result['publish_result'].get('web_url', 'Draft created')}")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
