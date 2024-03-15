import os
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
from dotenv import load_dotenv
from ..utils.embedding_utils import create_embedding, find_similar_embeddings

load_dotenv()
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
        generated_review = await generate_product_review(product_data)
        embedding = await create_embedding(generated_review)
        product_collection.update_one({"_id": product_id}, {"$set": {"generated_review": generated_review,
                                                                     "embedding": embedding}})
    except Exception as e:
        # Log the exception (logging mechanism to be configured as needed)
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred")


async def generate_product_review(product):
    try:
        # Read the prompt asynchronously
        async with aiofiles.open('prompts/review-prompt.txt', mode='r') as file:
            prompt = await file.read()

        # Configure your OpenAI client properly here
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",
                 "content": f"Generate a comprehensive report based on the following product data: {product}"}
            ]
        )
        message = completion.choices[0].message.model_dump()
        return message["content"]

    except Exception as e:
        # Log the exception (logging mechanism to be configured as needed)
        print(f"Error in generate_product_review: {e}")
        raise


@router.post("/scrape/amazon")
async def scrape_amazon(url: str):
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


@router.post("/generate-review")
async def generate_review(product: dict):
    client = OpenAI()
    # read prompt from the prompts folder
    prompt = ""
    with open('prompts/review-prompt.txt', 'r') as file:
        prompt = file.read()

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user",
             "content": "Generate a comprehensive report based on the following product data: " + str(product)}
        ]
    )

    return completion.choices[0].message


@router.post("/products")
async def create_product(product: dict):
    product_id = product_collection.insert_one(product).inserted_id
    product_result = product_collection.find_one({"_id": product_id})
    product_data = product_serializer(product_result)
    return product_data


@router.get("/products")
async def get_products(job_id: str = None):
    if job_id:
        # Fetch products by job_id if the query parameter is provided
        products_cursor = product_collection.find({"job_id": job_id})
        products = list_products_serializer(products_cursor)
    else:
        # Fetch all products if no job_id query parameter is provided
        products_cursor = product_collection.find({})
        products = list_products_serializer(products_cursor)

    return products if products else []


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = product_collection.find_one({"_id": ObjectId(product_id)})
    if product:
        return product_serializer(product)
    raise HTTPException(status_code=404, detail="Product not found")


@router.get("/query")
async def get_query(query: str):
    embedding = await create_embedding(query)
    excludes = [
        "reviews",
        "embedding",
        ]
    documents = await find_similar_embeddings(product_collection, embedding, excludes)
    return documents
