import asyncio
import subprocess
from datetime import datetime

from fastapi import APIRouter, HTTPException
from openai import OpenAI

from ..models.job import Job
from ..schemas.schemas import list_jobs_serializer, job_serializer, product_serializer, list_products_serializer
from ..config.database import job_collection
from ..config.database import product_collection
from ..config.database import test_collection

from bson import ObjectId
import aiofiles
from ..utils.embedding_utils import create_embedding, find_similar_embeddings
from ..utils.utils import extract_asin_from_url

router = APIRouter()


# Get all jobs
@router.get("/jobs")
async def get_jobs():
    jobs = list_jobs_serializer(job_collection.find())
    return jobs


# Get job by id
@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_collection.find_one({"_id": ObjectId(job_id)})
    if job:
        return job_serializer(job)
    raise HTTPException(status_code=404, detail="Job not found")


# Create job
@router.post("/jobs")
async def create_job(job: Job):
    job_json = job.model_dump(by_alias=True)
    job_json.pop("_id", None)
    if job_collection.find_one({"_id": job_json["_id"]}):
        raise HTTPException(status_code=400, detail="Job ID already exists")
    result = job_collection.insert_one(job_json)

    inserted_job = job_collection.find_one({"_id": result.inserted_id})
    return inserted_job


# Update job
@router.put("/jobs/{job_id}")
async def update_job(job_id: str, job: Job):
    try:
        # Update the job
        job = job.model_dump()
        job_collection.update_one({"_id": ObjectId(job_id)}, {"$set": job})
        product_data = job.get("result")
        if not product_data:
            raise HTTPException(status_code=400, detail="No product data found in job")
        product_id = product_data["id"]

        existing_product = product_collection.find_one({"_id": product_id})
        if existing_product:
            product_collection.update_one({"_id": product_id}, {"$set": product_data})
        else:
            product_collection.insert_one({
                "_id": product_id,
                **product_data
            })
            # Run generate_product_review and generate_embedding_text in parallel
        generated_review, embedding_text = await asyncio.gather(
            generate_product_review(product_data),
            generate_embedding_text(product_data)
        )

        # Now that we have embedding_text, we can generate the embedding
        embedding = await create_embedding(embedding_text)

        product_collection.update_one({"_id": product_id}, {"$set": {
            "generated_review": generated_review,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "updated_at": datetime.now()
        }})
    except Exception as e:
        # Log the exception (logging mechanism to be configured as needed)
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred")


async def generate_embedding_text(product):
    try:
        # Read the prompt asynchronously
        async with aiofiles.open('prompts/embedding_text_prompt.txt', mode='r') as file:
            prompt = await file.read()

        # Configure your OpenAI client properly here
        client = OpenAI()
        product.pop("embedding", None)
        product.pop("reviews", None)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    except Exception as e:
        # Log the exception (logging mechanism to be configured as needed)
        print(f"Error in generate_product_review: {e}")
        raise


async def generate_product_review(product):
    try:
        # Read the prompt asynchronously
        # check the length of the product review array
        promptFile = "prompts/reviews_prompt.txt"
        if len(product["reviews"]) == 0:
            promptFile = "prompts/no_reviews_prompt.txt"
        async with aiofiles.open(promptFile, mode='r') as file:
            prompt = await file.read()

        product.pop("embedding", None)
        # Configure your OpenAI client properly here
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    except Exception as e:
        # Log the exception (logging mechanism to be configured as needed)
        print(f"Error in generate_product_review: {e}")
        raise


@router.post("/scrape/amazon")
async def scrape_amazon(body: dict):
    url = body.get("url")
    # get the product id from the url
    asin = extract_asin_from_url(url)
    if not asin:
        raise HTTPException(status_code=400, detail="Invalid Amazon product URL")
    # check if the product already exists
    existing_product = product_collection.find_one({"_id": asin}, {"embedding": 0, "reviews": 0})
    if existing_product:
        return existing_product

    job = Job(url=url)
    job = job.model_dump(by_alias=True)
    job.pop("_id", None)
    job_id = job_collection.insert_one(job).inserted_id
    job_result = job_collection.find_one({"_id": job_id})
    job_data = job_serializer(job_result)

    # Start Scrapy spider as a separate process
    url = job["url"]
    command = ["scrapy", "crawl", "amazon", "-a", f"url={url}", "-a", f"job_id={job_id}"]

    # print current working directory
    subprocess.Popen(command, cwd="scrapy-project")
    return job_data


@router.post("/products")
async def create_product(product: dict):
    product_id = product_collection.insert_one(product).inserted_id
    product_result = product_collection.find_one({"_id": product_id})
    product_data = product_serializer(product_result)
    return product_data


@router.get("/product_regenerate")
async def regenerate_product(id: str):
    product = product_collection.find_one({"_id": id})
    if product:
        # Run generate_product_review and generate_embedding_text in parallel
        generated_review, embedding_text = await asyncio.gather(
            generate_product_review(product),
            generate_embedding_text(product)
        )

        # Now that we have embedding_text, we can generate the embedding
        embedding = await create_embedding(embedding_text)

        product_collection.update_one({"_id": id}, {"$set": {
            "generated_review": generated_review,
            "embedding": embedding,
            "embedding_text": embedding_text,
            "updated_at": datetime.now()
        }})
        return product_collection.find_one({"_id": id}, {"embedding": 0, "reviews": 0})
    raise HTTPException(status_code=404, detail="Product not found")


@router.get("/products")
async def get_products(job_id: str = None):
    if job_id:
        products_cursor = product_collection.find({"job_id": job_id}, {"embedding": 0, "reviews": 0})
    else:
        # Fetch all products if no job_id query parameter is provided
        products_cursor = product_collection.find({}, {"embedding": 0, "reviews": 0})

    return list(products_cursor)


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = product_collection.find_one({"_id": product_id}, {"embedding": 0, "reviews": 0})
    if product:
        return product
    raise HTTPException(status_code=404, detail="Product not found")


@router.post("/embeddings/search")
async def get_query(body: dict):
    query = body.get("query")
    embedding = await create_embedding(query)
    excludes = [
        "embedding",
        "reviews"
    ]
    documents = await find_similar_embeddings(product_collection, embedding, excludes)
    # items = []
    # for doc in documents:
    #     item = {
    #         "title": doc["title"],
    #         "score": doc["score"]
    #     }
    #     items.append(item)
    return list(documents)


@router.post("/products/{product_id}/chat")
async def get_product_chat(product_id: str, body: dict):
    query = body.get("query")
    product = product_collection.find_one({"_id": product_id})
    if product:
        # Read the prompt asynchronously
        async with aiofiles.open('prompts/product_chat_prompt.txt', mode='r') as file:
            prompt = await file.read()

        # Configure your OpenAI client properly here
        client = OpenAI()
        product.pop("embedding", None)
        # product.pop("reviews", None)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"{product}"},
                {"role": "user", "content": query}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]
    raise HTTPException(status_code=404, detail="Product not found")
