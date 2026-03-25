# Voice Agent - Current Implementation Status

This repository currently has the backend ingestion flow implemented for PDF uploads.

## Completed Status

- FastAPI service bootstrapped with CORS support.
- Health endpoint is implemented: `GET /api/health`.
- Upload endpoint is implemented: `POST /api/upload`.
- Full ingestion pipeline is working for upload requests:
	- Validate incoming file metadata and PDF type.
	- Save file to temporary upload folder.
	- Extract text page-by-page from PDF.
	- Chunk extracted text using token window + overlap.
	- Generate embeddings with Gemini embedding model.
	- Upsert chunk documents into MongoDB.
	- Return `paper_id`, `chunk_count`, and status.
- MongoDB connection bootstrap + startup index creation are implemented.

## Implemented Flow (As Of Now)

1. Client sends a PDF to `POST /api/upload`.
2. API validates filename, extension/content type, and max file size.
3. PDF is saved in `.tmp/uploads`.
4. Text is extracted per page.
5. Text is split into chunks (default: 500 tokens, overlap 50).
6. Embeddings are generated in batches through Gemini.
7. Documents are upserted to MongoDB `chunks` collection.
8. API returns:

```json
{
	"paper_id": "<uuid>",
	"chunk_count": 42,
	"status": "uploaded"
}
```

## Current API Surface

- `GET /api/health`
	- Response: `{ "status": "ok" }`

- `POST /api/upload`
	- Form field: `file` (PDF)
	- Response model:

```json
{
	"paper_id": "string",
	"chunk_count": 0,
	"status": "uploaded"
}
```

## Configuration

Required environment variables:

- `GEMINI_API_KEY`
- `MONGODB_URI`

Important defaults in backend settings:

- `chunk_size_tokens=500`
- `chunk_overlap_tokens=50`
- `embedding_model=models/gemini-embedding-001`
- `embedding_dimension=3072`
- `max_upload_file_size_mb=20`

## Run Backend (Local)

From project root:

```powershell
cd backend
uvicorn app.main:app --reload --port 8001
```

Health check:

```powershell
curl http://127.0.0.1:8001/api/health
```

Upload test:

```powershell
curl -X POST "http://127.0.0.1:8001/api/upload" ^
	-H "accept: application/json" ^
	-F "file=@sample.pdf;type=application/pdf"
```

## Not Completed Yet

- Query / retrieval endpoint logic is not wired yet.
- `app/api/query.py` exists but is currently empty.
- Separate test files exist under `tests/` but are currently placeholders.

## Notes

- On startup, the app checks MongoDB availability and creates chunk indexes.
- Upload endpoint includes retry/error handling for transient embedding failures.