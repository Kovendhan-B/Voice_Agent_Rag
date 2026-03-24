from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	gemini_api_key: str = Field(alias="GEMINI_API_KEY")
	mongodb_uri: str = Field(alias="MONGODB_URI")

	mongodb_db: str = "voice_research"
	mongodb_chunks_collection: str = "chunks"

	chunk_size_tokens: int = 500
	chunk_overlap_tokens: int = 50

	embedding_model: str = "models/text-embedding-004"
	embedding_dimension: int = 768

	temp_upload_dir: str = ".tmp/uploads"
	cors_origins: list[str] = ["*"]

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
		populate_by_name=True,
	)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings()
