from pymongo import MongoClient
from pymongo.collection import Collection

from app.config import get_settings

_mongo_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
	global _mongo_client
	if _mongo_client is None:
		settings = get_settings()
		_mongo_client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
	return _mongo_client


def get_chunks_collection() -> Collection:
	settings = get_settings()
	db = get_mongo_client()[settings.mongodb_db]
	return db[settings.mongodb_chunks_collection]
