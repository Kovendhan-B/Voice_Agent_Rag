import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.db.mongo import get_chunks_collection
from app.models.schemas import UploadResponse
from app.services.chunker import chunk_pages
from app.services.embedder import (
	EmbeddingValidationError,
	GeminiEmbedder,
	RetryableEmbeddingError,
)
from app.services.pdf_processor import extract_text_by_page
from app.services.vector_store import build_chunk_documents, upsert_chunk_documents

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
	# 1) Receive file and 2) validate type.
	if not file.filename:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")

	suffix = Path(file.filename).suffix.lower()
	if suffix != ".pdf":
		raise HTTPException(
			status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
			detail="Only PDF files are supported.",
		)
	if file.content_type not in {"application/pdf", "application/octet-stream"}:
		raise HTTPException(
			status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
			detail="Invalid content type. Expected application/pdf.",
		)

	settings = get_settings()
	temp_dir = Path(settings.temp_upload_dir)
	temp_dir.mkdir(parents=True, exist_ok=True)
	temp_file_path: Path | None = None

	try:
		# 3) Save to temp.
		with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=temp_dir) as tmp:
			temp_file_path = Path(tmp.name)
			content = await file.read()
			if not content:
				raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail="Uploaded file is empty.",
				)
			max_size_bytes = settings.max_upload_file_size_mb * 1024 * 1024
			if len(content) > max_size_bytes:
				raise HTTPException(
					status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
					detail=f"Uploaded file exceeds {settings.max_upload_file_size_mb} MB limit.",
				)
			tmp.write(content)

		# 4) Extract text per page.
		page_text = extract_text_by_page(temp_file_path)

		# 5) Chunk using PRD values from settings (defaults: 500 tokens, overlap 50).
		chunks = chunk_pages(
			pages=page_text,
			chunk_size_tokens=settings.chunk_size_tokens,
			overlap_tokens=settings.chunk_overlap_tokens,
		)
		if not chunks:
			raise HTTPException(
				status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
				detail="No chunks could be created from this PDF.",
			)

		# 6) Generate embeddings.
		embedder = GeminiEmbedder(
			api_key=settings.gemini_api_key,
			model=settings.embedding_model,
			expected_dimension=settings.embedding_dimension,
			max_retries=settings.embedding_max_retries,
			retry_base_delay_sec=settings.embedding_retry_base_delay_sec,
			rate_limit_per_minute=settings.embedding_rate_limit_per_minute,
		)
		embeddings = embedder.embed_texts(
			[str(chunk["text"]) for chunk in chunks],
			batch_size=settings.embedding_batch_size,
		)

		# 7) Insert many chunk documents into Mongo.
		paper_id = str(uuid4())
		documents = build_chunk_documents(
			paper_id=paper_id,
			chunks=chunks,
			embeddings=embeddings,
		)
		collection = get_chunks_collection()
		inserted_count = upsert_chunk_documents(collection, documents)

		# 8) Return response.
		return UploadResponse(
			paper_id=paper_id,
			chunk_count=inserted_count,
			status="uploaded",
		)
	except RetryableEmbeddingError as exc:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail=f"Embedding service temporarily unavailable: {exc}",
		) from exc
	except EmbeddingValidationError as exc:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail=f"Embedding validation failed: {exc}",
		) from exc
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Upload pipeline failed: {exc}",
		) from exc
	finally:
		await file.close()
		if temp_file_path and temp_file_path.exists():
			temp_file_path.unlink(missing_ok=True)
