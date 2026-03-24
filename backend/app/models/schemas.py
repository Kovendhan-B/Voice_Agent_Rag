from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
	paper_id: str
	chunk_count: int = Field(ge=0)
	status: str = "uploaded"


class ChunkPayload(BaseModel):
	chunk_index: int = Field(ge=0)
	text: str
	page: int = Field(ge=1)


class ChunkDocument(ChunkPayload):
	paper_id: str
	embedding: list[float]
	created_at: datetime
