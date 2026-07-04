import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
from loguru import logger

from app.config import settings


@dataclass
class TopicRow:
    id: int
    title: str
    reason: str | None
    score: float
    generated_at: datetime
    selected: bool


@dataclass
class ArticleRow:
    id: int
    topic_id: int | None
    title: str
    excerpt: str | None
    markdown: str
    html: str
    slug: str
    meta_description: str | None
    keywords: list[str]
    tags: list[str]
    status: str
    beehiiv_post_id: str | None
    created_at: datetime
    published_at: datetime | None


@dataclass
class RunRow:
    id: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    runtime_seconds: float | None
    error_message: str | None
    error_stage: str | None
    tokens_used: int
    cost_usd: float
    article_id: int | None


@dataclass
class AffiliateRow:
    id: int
    tool_name: str
    affiliate_url: str
    category: str | None
    is_active: bool
    created_at: datetime


@dataclass
class AssetRow:
    id: int
    article_id: int | None
    asset_type: str
    file_path: str
    url: str | None
    prompt: str | None
    metadata: dict[str, Any]
    created_at: datetime


class Database:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()
        logger.info("Database initialized", path=str(self.db_path))

    @asynccontextmanager
    async def connect(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def execute(self, query: str, params: tuple = ()) -> None:
        async with self.connect() as db:
            await db.execute(query, params)
            await db.commit()

    async def fetchone(self, query: str, params: tuple = ()) -> aiosqlite.Row | None:
        async with self.connect() as db:
            cursor = await db.execute(query, params)
            return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()) -> list[aiosqlite.Row]:
        async with self.connect() as db:
            cursor = await db.execute(query, params)
            return await cursor.fetchall()

    # Topics
    async def create_topic(self, title: str, reason: str | None, score: float) -> int:
        async with self.connect() as db:
            cursor = await db.execute(
                "INSERT INTO topics (title, reason, score) VALUES (?, ?, ?)",
                (title, reason, score),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_topic(self, topic_id: int) -> TopicRow | None:
        row = await self.fetchone("SELECT * FROM topics WHERE id = ?", (topic_id,))
        return TopicRow(**row) if row else None

    async def get_selected_topic(self) -> TopicRow | None:
        row = await self.fetchone("SELECT * FROM topics WHERE selected = 1 ORDER BY generated_at DESC LIMIT 1")
        return TopicRow(**row) if row else None

    async def mark_topic_selected(self, topic_id: int) -> None:
        await self.execute("UPDATE topics SET selected = 1 WHERE id = ?", (topic_id,))

    async def get_recent_topics(self, limit: int = 20) -> list[TopicRow]:
        rows = await self.fetchall("SELECT * FROM topics ORDER BY generated_at DESC LIMIT ?", (limit,))
        return [TopicRow(**row) for row in rows]

    # Articles
    async def create_article(
        self,
        topic_id: int | None,
        title: str,
        excerpt: str | None,
        markdown: str,
        html: str,
        slug: str,
        meta_description: str | None,
        keywords: list[str],
        tags: list[str],
        status: str = "draft",
    ) -> int:
        async with self.connect() as db:
            cursor = await db.execute(
                """
                INSERT INTO articles (topic_id, title, excerpt, markdown, html, slug, meta_description, keywords, tags, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (topic_id, title, excerpt, markdown, html, slug, meta_description, json.dumps(keywords), json.dumps(tags), status),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_article(self, article_id: int) -> ArticleRow | None:
        row = await self.fetchone("SELECT * FROM articles WHERE id = ?", (article_id,))
        if not row:
            return None
        data = dict(row)
        data["keywords"] = json.loads(data["keywords"] or "[]")
        data["tags"] = json.loads(data["tags"] or "[]")
        return ArticleRow(**data)

    async def get_article_by_slug(self, slug: str) -> ArticleRow | None:
        row = await self.fetchone("SELECT * FROM articles WHERE slug = ?", (slug,))
        if not row:
            return None
        data = dict(row)
        data["keywords"] = json.loads(data["keywords"] or "[]")
        data["tags"] = json.loads(data["tags"] or "[]")
        return ArticleRow(**data)

    async def update_article_status(self, article_id: int, status: str, beehiiv_post_id: str | None = None) -> None:
        if beehiiv_post_id:
            await self.execute(
                "UPDATE articles SET status = ?, beehiiv_post_id = ?, published_at = ? WHERE id = ?",
                (status, beehiiv_post_id, datetime.now(), article_id),
            )
        else:
            await self.execute("UPDATE articles SET status = ? WHERE id = ?", (status, article_id))

    async def get_recent_articles(self, limit: int = 10) -> list[ArticleRow]:
        rows = await self.fetchall("SELECT * FROM articles ORDER BY created_at DESC LIMIT ?", (limit,))
        articles = []
        for row in rows:
            data = dict(row)
            data["keywords"] = json.loads(data["keywords"] or "[]")
            data["tags"] = json.loads(data["tags"] or "[]")
            articles.append(ArticleRow(**data))
        return articles

    # Runs
    async def create_run(self) -> int:
        async with self.connect() as db:
            cursor = await db.execute(
                "INSERT INTO runs (status) VALUES (?)",
                ("running",),
            )
            await db.commit()
            return cursor.lastrowid

    async def update_run(
        self,
        run_id: int,
        status: str,
        runtime_seconds: float | None = None,
        error_message: str | None = None,
        error_stage: str | None = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        article_id: int | None = None,
    ) -> None:
        completed_at = datetime.now() if status in ("completed", "failed") else None
        await self.execute(
            """
            UPDATE runs
            SET status = ?, completed_at = ?, runtime_seconds = ?, error_message = ?, error_stage = ?, tokens_used = ?, cost_usd = ?, article_id = ?
            WHERE id = ?
            """,
            (status, completed_at, runtime_seconds, error_message, error_stage, tokens_used, cost_usd, article_id, run_id),
        )

    async def get_run(self, run_id: int) -> RunRow | None:
        row = await self.fetchone("SELECT * FROM runs WHERE id = ?", (run_id,))
        return RunRow(**row) if row else None

    async def get_recent_runs(self, limit: int = 10) -> list[RunRow]:
        rows = await self.fetchall("SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,))
        return [RunRow(**row) for row in rows]

    # Affiliate links
    async def create_affiliate_link(self, tool_name: str, affiliate_url: str, category: str | None = None) -> int:
        async with self.connect() as db:
            cursor = await db.execute(
                "INSERT OR REPLACE INTO affiliate_links (tool_name, affiliate_url, category) VALUES (?, ?, ?)",
                (tool_name, affiliate_url, category),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_affiliate_link(self, tool_name: str) -> AffiliateRow | None:
        row = await self.fetchone("SELECT * FROM affiliate_links WHERE tool_name = ? AND is_active = 1", (tool_name,))
        return AffiliateRow(**row) if row else None

    async def get_affiliate_links(self, category: str | None = None) -> list[AffiliateRow]:
        if category:
            rows = await self.fetchall("SELECT * FROM affiliate_links WHERE category = ? AND is_active = 1", (category,))
        else:
            rows = await self.fetchall("SELECT * FROM affiliate_links WHERE is_active = 1")
        return [AffiliateRow(**row) for row in rows]

    async def bulk_insert_affiliate_links(self, links: list[dict]) -> int:
        count = 0
        async with self.connect() as db:
            for link in links:
                await db.execute(
                    "INSERT OR REPLACE INTO affiliate_links (tool_name, affiliate_url, category) VALUES (?, ?, ?)",
                    (link["tool_name"], link["affiliate_url"], link.get("category")),
                )
                count += 1
            await db.commit()
        return count

    # Assets
    async def create_asset(
        self,
        article_id: int | None,
        asset_type: str,
        file_path: str,
        url: str | None = None,
        prompt: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        async with self.connect() as db:
            cursor = await db.execute(
                """
                INSERT INTO assets (article_id, asset_type, file_path, url, prompt, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (article_id, asset_type, file_path, url, prompt, json.dumps(metadata or {})),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_assets_for_article(self, article_id: int) -> list[AssetRow]:
        rows = await self.fetchall("SELECT * FROM assets WHERE article_id = ?", (article_id,))
        assets = []
        for row in rows:
            data = dict(row)
            data["metadata"] = json.loads(data["metadata"] or "{}")
            assets.append(AssetRow(**data))
        return assets

    # Settings
    async def set_setting(self, key: str, value: str) -> None:
        await self.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now()),
        )

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = await self.fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else default


SCHEMA = """
-- Topics table: stores discovered and ranked topics
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    reason TEXT,
    score REAL NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    selected BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_topics_generated_at ON topics(generated_at);
CREATE INDEX IF NOT EXISTS idx_topics_selected ON topics(selected);

-- Articles table: stores generated articles
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER REFERENCES topics(id),
    title TEXT NOT NULL,
    excerpt TEXT,
    markdown TEXT NOT NULL,
    html TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    meta_description TEXT,
    keywords TEXT,
    tags TEXT,
    status TEXT DEFAULT 'draft',
    beehiiv_post_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_topic_id ON articles(topic_id);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);

-- Runs table: tracks pipeline execution
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    runtime_seconds REAL,
    error_message TEXT,
    error_stage TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    article_id INTEGER REFERENCES articles(id)
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);

-- Affiliate links table
CREATE TABLE IF NOT EXISTS affiliate_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL UNIQUE,
    affiliate_url TEXT NOT NULL,
    category TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_affiliate_tool_name ON affiliate_links(tool_name);
CREATE INDEX IF NOT EXISTS idx_affiliate_category ON affiliate_links(category);

-- Assets table: stores generated images and other assets
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES articles(id),
    asset_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    url TEXT,
    prompt TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assets_article_id ON assets(article_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);

-- Settings table: key-value store for runtime configuration
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


_db: Database | None = None


def get_database() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


async def init_database() -> Database:
    db = get_database()
    await db.init()
    return db
