from pymongo.mongo_client import MongoClient
from app.core.config import settings

uri = settings.MONGODB_CONNECTION_STRING
client = MongoClient(uri)
db = client.scraper

ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"

product_collection = db["products"]
