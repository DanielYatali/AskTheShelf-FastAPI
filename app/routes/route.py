import os
import subprocess
from datetime import datetime

from fastapi import APIRouter, HTTPException
from openai import OpenAI

from ..models.job import Job
from ..schemas.schemas import list_jobs_serializer, job_serializer, product_serializer, list_products_serializer
from ..config.database import job_collection
from ..config.database import product_collection
from bson import ObjectId
import aiofiles
# import the env variables
from dotenv import load_dotenv

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
async def create_job(job: dict):
    job_id = job_collection.insert_one(job).inserted_id
    job = job_collection.find_one({"_id": job_id})
    return job_serializer(job)


# Update job
@router.put("/jobs/{job_id}")
async def update_job(job_id: str, job: dict):
    try:
        # Update the job
        job_collection.update_one({"_id": ObjectId(job_id)}, {"$set": job})
        product_data = job.get("result")

        if not product_data:
            raise HTTPException(status_code=400, detail="No product data found in job")

        generated_review = await generate_product_review(product_data)
        product_data["generated_review"] = generated_review
        # Create a new product
        product_id = product_collection.insert_one(product_data).inserted_id
        return {
            "success": True,
        }
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


# async def update_job(job_id: str, job: dict):
#     # Update the job
#     job_collection.update_one({"_id": ObjectId(job_id)}, {"$set": job})
#     product = job["result"]
#     job = job_collection.find_one({"_id": ObjectId(job_id)})
#     # Create a new product
#     product_id = product_collection.insert_one(product).inserted_id
#     product = product_collection.find_one({"_id": product_id})
#
#     # Generate a review
#     client = OpenAI()
#     # read prompt from the prompts folder
#     prompt = ""
#     with open('prompts/review-prompt.txt', 'r') as file:
#         prompt = file.read()
#
#     completion = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": prompt},
#             {"role": "user",
#              "content": "Generate a comprehensive report based on the following product data: " + str(product)}
#         ]
#     )
#     result = completion.choices[0].message
#
#     product_collection.update_one({"_id": ObjectId(product_id)},
#                                   {"$set": {"generated_review": result}})
#     product = product_collection.find_one({"_id": ObjectId(product_id)})
#     return product


@router.post("/scrape/amazon")
async def scrape_amazon(job: dict):
    job["status"] = "started"
    job["start_time"] = str(datetime.utcnow())
    job["end_time"] = ""
    job["result"] = {}
    job["error"] = {}

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
