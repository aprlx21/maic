from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MAIC_", env_file=".env", extra="ignore")
    mode: Literal["demo", "openai"] = "demo"
    model: str = "gpt-6-luna"
    data_dir: Path = ROOT / "data"
    database_url: str = "sqlite:///./data/app.db"
    checkpoint_url: str = "sqlite:///./data/checkpoints.db"
    storage: Literal["local", "minio"] = "local"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "maic"
    minio_secret_key: str = "maic-local-development"
    minio_bucket: str = "maic"
    minio_secure: bool = False
    max_pdf_mb: int = Field(default=30, ge=1, le=500)
    max_pages: int = Field(default=100, ge=1, le=1000)
    max_slides: int = Field(default=20, ge=3, le=60)
    max_auto_rounds: int = Field(default=0, ge=0, le=2)
    max_model_calls: int = Field(default=90, ge=1)
    max_input_tokens: int = Field(default=1_000_000, ge=1)
    max_output_tokens: int = Field(default=40_000, ge=1)
    max_call_input_tokens: int = Field(default=32_000, ge=1)
    max_call_output_tokens: int = Field(default=12_000, ge=16)
    max_job_seconds: int = 1800
    context_tokens: int = Field(default=4000, ge=1)
    script_batch_size: int = Field(default=8, ge=1, le=8)
    image_model: str = "gpt-image-2"
    max_slide_images: int = Field(default=6, ge=0, le=20)
    max_ai_images: int = Field(default=2, ge=0, le=10)
    input_usd_per_million: float | None = None
    cached_input_usd_per_million: float | None = None
    output_usd_per_million: float | None = None
    soffice: str = ""
    tessdata_prefix: str = ""
    ocr_languages: str = "vie+eng"
    slide_font: str = "Noto Sans"

    @field_validator("input_usd_per_million", "cached_input_usd_per_million", "output_usd_per_million", mode="before")
    @classmethod
    def blank_rate(cls, value):
        return None if value == "" else value

    @property
    def vendor(self) -> Path:
        return ROOT / "vendor/slides_maker/skills/slide-maker"


@lru_cache
def settings() -> Settings:
    result = Settings()
    result.data_dir = result.data_dir.resolve()
    result.data_dir.mkdir(parents=True, exist_ok=True)
    local_tessdata = result.data_dir / "tessdata"
    if not result.tessdata_prefix and all((local_tessdata / f"{lang}.traineddata").is_file()
                                         for lang in result.ocr_languages.split("+")):
        result.tessdata_prefix = str(local_tessdata)
    return result
