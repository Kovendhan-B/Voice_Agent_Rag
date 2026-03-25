from pymongo import ASCENDING
from pymongo.collection import Collection


def create_chunk_indexes(collection: Collection) -> None:
	collection.create_index([("paper_id", ASCENDING)], name="idx_paper_id")
	collection.create_index(
		[("paper_id", ASCENDING), ("chunk_index", ASCENDING)],
		name="uniq_paper_chunk",
		unique=True,
	)
	collection.create_index([("created_at", ASCENDING)], name="idx_created_at")
