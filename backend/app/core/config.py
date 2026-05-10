import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


class Settings(BaseSettings):
    project_name: str = "AI Legal Chambers API"
    project_version: str = "0.6.0"
    api_prefix: str = "/api"
    database_url: str = Field(
        default=f"sqlite:///{(PROJECT_ROOT / 'backend' / 'dev.db').as_posix()}",
    )
    uploads_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "uploads"),
    )
    crawl_storage_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "crawl_storage"),
    )
    corpus_exports_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "exports" / "corpus"),
    )
    tier1_data_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "data" / "tier1"),
    )
    tier1_raw_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "data" / "tier1" / "raw"),
    )
    tier1_processed_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "data" / "tier1" / "processed"),
    )
    tier1_label_audit_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "data" / "tier1" / "label_audit"),
    )
    training_export_dir: str = Field(
        default=str(PROJECT_ROOT / "training_export"),
    )
    kaggle_username: str = ""
    kaggle_key: str = ""
    hf_token: str = ""
    ml_artifacts_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "ml_artifacts"),
    )
    retrieval_artifacts_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "ml_artifacts" / "retrieval"),
    )
    crawl_seed_dir: str = Field(
        default=str(PROJECT_ROOT / "backend" / "app" / "seed" / "crawl_sources"),
    )
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    llm_provider: str = "local"
    llm_provider_label: str = "Chamber Local Intelligence"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_web_search_model: str = "gpt-4o-mini"
    live_web_search_enabled: bool = False
    llm_drafting_enabled: bool = False
    search_provider: str = "openai"
    tavily_api_key: str = ""
    serpapi_api_key: str = ""
    bing_search_api_key: str = ""
    google_cse_api_key: str = ""
    google_cse_id: str = ""
    web_search_max_results: int = 8
    web_search_timeout_seconds: int = 30
    web_source_fetch_timeout_seconds: int = 20
    ml_transformer_model_name: str = "distilbert-base-multilingual-cased"
    ml_transformer_strong_model_name: str = "xlm-roberta-base"
    ml_transformer_max_length: int = 256
    ml_transformer_epochs: int = 1
    ml_transformer_batch_size: int = 4
    ml_hybrid_epochs: int = 12
    ml_hybrid_batch_size: int = 8
    ml_default_inference_family: str = "Baseline"
    ml_embedding_model_name: str = "distilbert-base-multilingual-cased"
    semantic_query_mode: str = "fast"
    semantic_index_batch_size: int = 8
    semantic_retrieval_top_k: int = 10
    tesseract_cmd: str = "tesseract"
    ocr_default_languages: str = "eng"
    cors_origins: str = Field(default=",".join(DEFAULT_CORS_ORIGINS))

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        raw_value = self.cors_origins.strip()
        if not raw_value:
            return DEFAULT_CORS_ORIGINS

        if raw_value.startswith("["):
            try:
                parsed = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed = []
            if isinstance(parsed, list):
                return list(
                    dict.fromkeys(str(item).strip().strip("\"'") for item in parsed if str(item).strip())
                )

        return list(
            dict.fromkeys(item.strip().strip("\"'") for item in raw_value.split(",") if item.strip())
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
