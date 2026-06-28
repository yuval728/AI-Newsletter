from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    beehiiv_api_key: str = Field(..., alias="BEEHIIV_API_KEY")
    publication_id: str = Field(..., alias="PUBLICATION_ID")
    pollinations_key: str | None = Field(default=None, alias="POLLINATIONS_KEY")

    database_path: Path = Field(default=Path("data/newsletter.db"))
    assets_dir: Path = Field(default=Path("assets"))
    logs_dir: Path = Field(default=Path("logs"))

    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.7, alias="GEMINI_TEMPERATURE")
    gemini_max_tokens: int = Field(default=8192, alias="GEMINI_MAX_TOKENS")

    beehiiv_base_url: str = Field(default="https://api.beehiiv.com/v2", alias="BEEHIIV_BASE_URL")

    image_model: str = Field(default="gptimage", alias="IMAGE_MODEL")
    image_width: int = Field(default=1200, alias="IMAGE_WIDTH")
    image_height: int = Field(default=630, alias="IMAGE_HEIGHT")

    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_backoff: float = Field(default=2.0, alias="RETRY_BACKOFF")
    request_timeout: int = Field(default=120, alias="REQUEST_TIMEOUT")

    auto_publish: bool = Field(default=True, alias="AUTO_PUBLISH")
    dry_run: bool = Field(default=False, alias="DRY_RUN")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    @property
    def assets_images_dir(self) -> Path:
        return self.assets_dir / "images"

    @property
    def assets_logos_dir(self) -> Path:
        return self.assets_dir / "logos"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()