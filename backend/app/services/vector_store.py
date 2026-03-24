from datetime import datetime, timezone

from pymongo.collection import Collection


def build_chunk_documents(
	paper_id: str,
	chunks: list[dict[str, int | str]],
	embeddings: list[list[float]],
) -> list[dict]:
	if len(chunks) != len(embeddings):
		raise ValueError("Chunk and embedding counts must match.")

	created_at = datetime.now(timezone.utc)
	documents: list[dict] = []

	for chunk, embedding in zip(chunks, embeddings):
		documents.append(
			{
				"paper_id": paper_id,
				"chunk_index": int(chunk["chunk_index"]),
				"text": str(chunk["text"]),
				"embedding": embedding,
				"page": int(chunk["page"]),
				"created_at": created_at,
			}
		)

	return documents


def insert_chunk_documents(collection: Collection, documents: list[dict]) -> int:
	if not documents:
		return 0

	result = collection.insert_many(documents, ordered=True)
	return len(result.inserted_ids)
