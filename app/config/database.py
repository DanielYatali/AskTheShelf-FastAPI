from pymongo.mongo_client import MongoClient
uri = "mongodb+srv://Scraper:TzQkvr6fydIK233S@scraper.3d1axyn.mongodb.net/?retryWrites=true&w=majority&appName=scraper"
# Create a new client and connect to the server
client = MongoClient(uri)
db = client.scraper

job_collection = db["job_collection"]
product_collection = db["product_collection"]




