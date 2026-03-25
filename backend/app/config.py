from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	gemini_api_key: str = Field(alias="GEMINI_API_KEY")
	mongodb_uri: str = Field(alias="MONGODB_URI")

	mongodb_db: str = "voice_research"
	mongodb_chunks_collection: str = "chunks"

	chunk_size_tokens: int = 500
	chunk_overlap_tokens: int = 50

	embedding_model: str = "models/gemini-embedding-001"
	embedding_dimension: int = 3072
	embedding_batch_size: int = 32
	embedding_max_retries: int = 3
	embedding_retry_base_delay_sec: float = 1.0
	embedding_rate_limit_per_minute: int = 240
	max_upload_file_size_mb: int = 20
	mongodb_server_selection_timeout_ms: int = 5000

	temp_upload_dir: str = ".tmp/uploads"
	cors_origins: list[str] = ["*"]

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
		populate_by_name=True,
	)

	@model_validator(mode="after")
	def validate_runtime_limits(self) -> "Settings":
		if self.embedding_batch_size <= 0:
			raise ValueError("embedding_batch_size must be > 0")
		if self.embedding_max_retries < 1:
			raise ValueError("embedding_max_retries must be >= 1")
		if self.embedding_retry_base_delay_sec <= 0:
			raise ValueError("embedding_retry_base_delay_sec must be > 0")
		if self.embedding_rate_limit_per_minute <= 0:
			raise ValueError("embedding_rate_limit_per_minute must be > 0")
		if self.max_upload_file_size_mb <= 0:
			raise ValueError("max_upload_file_size_mb must be > 0")
		return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings()
