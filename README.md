# AI Newsletter Automation v1

Fully automated AI newsletter generation system that researches current topics, writes high-quality content, and publishes to Beehiiv.

## Features

- **Automated Topic Discovery**: Finds trending AI news using Google Search grounding
- **Smart Topic Ranking**: Multi-criteria scoring (search interest, novelty, affiliate potential, SEO, audience fit)
- **Deep Research**: Gemini with Google Search grounding for facts, sources, and quotes
- **Structured Writing**: Outline → Draft → Edit pipeline with quality checks
- **SEO Optimization**: Meta descriptions, slugs, keywords, and tags
- **Affiliate Link Insertion**: Automatic linking of mentioned tools
- **Featured Image Generation**: Pollinations.ai for custom illustrations
- **Beehiiv Publishing**: Creates and publishes drafts automatically
- **Full Logging & Monitoring**: Structured JSON logs, run tracking, error handling

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Gemini API key
- Beehiiv API key and Publication ID

### Installation

```bash
# Clone and install
git clone <repo>
cd AI-Newsletter
uv sync

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
GOOGLE_API_KEY=your_gemini_api_key
BEEHIIV_API_KEY=your_beehiiv_api_key
PUBLICATION_ID=your_publication_id
# Optional
POLLINATIONS_KEY=your_pollinations_key
```

### Running

```bash
# Full pipeline (publishes to Beehiiv)
uv run python -m app.main

# Dry run (creates draft only)
uv run python -m app.main --dry-run

# Custom topic
uv run python -m app.main --topic "Your custom topic"

# Seed affiliate links only
uv run python -m app.main --seed
```

### GitHub Actions

The workflow runs daily at 09:00 UTC. Add these secrets to your repository:
- `GOOGLE_API_KEY`
- `BEEHIIV_API_KEY`
- `PUBLICATION_ID`
- `POLLINATIONS_KEY` (optional)

## Architecture

```
Scheduler (GitHub Actions)
        │
        ▼
Pipeline Orchestrator
        │
├── Topic Discovery → Topic Ranking
├── Research → Outline → Writing → Editing
├── SEO → Affiliate Links → Image Generation
└── Beehiiv Publishing
```

## Project Structure

```
newsletter-ai/
├── .github/workflows/      # GitHub Actions
├── app/
│   ├── agents/            # 10 pipeline agents
│   ├── models/            # Pydantic models
│   ├── prompts/           # Agent prompts
│   ├── services/          # External service wrappers
│   ├── templates/         # Jinja2 HTML templates
│   ├── utils/             # Logging, helpers
│   ├── config.py          # Settings management
│   ├── pipeline.py        # Orchestrator
│   └── main.py            # CLI entry point
├── seeds/                 # Affiliate link seeds
├── tests/                 # Unit tests
├── pyproject.toml         # Dependencies
└── .env.example           # Config template
```

## Pipeline Stages

| Stage | Agent | Input | Output |
|-------|-------|-------|--------|
| 1 | Topic Discovery | — | 15-20 TopicCandidates |
| 2 | Topic Ranking | Candidates | 1 Topic |
| 3 | Research | Topic | Research (facts, sources, quotes) |
| 4 | Outline | Topic + Research | Structured Outline |
| 5 | Writing | Outline + Research | ArticleDraft |
| 6 | Editing | ArticleDraft | Polished ArticleDraft |
| 7 | SEO | ArticleDraft + Topic | SEOData |
| 8 | Affiliate | ArticleDraft | AffiliateResult |
| 9 | Image | Title + Summary | ImageAsset |
| 10 | Publishing | Final Article | PublishResult |

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check app/ tests/

# Type check
uv run mypy app/

# Format
uv run ruff format app/ tests/
```

## Logging

Logs are written to `logs/` directory with JSON format for analysis:
- API calls and responses
- Prompt versions
- Stage timing and token usage
- Errors and retries
- Publishing status

## Database

SQLite database (`newsletter.db`) tracks:
- `topics` - Discovered and selected topics
- `articles` - Generated articles with metadata
- `runs` - Pipeline execution history
- `affiliate_links` - Tool affiliate URLs
- `assets` - Generated images
- `settings` - Runtime configuration

## License

MIT