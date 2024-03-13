from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .routes.route import router

app = FastAPI()
# Define a list of allowed origins for CORS
# It's better to specify the exact domains in a production environment
allowed_origins = [
    "http://localhost:3000",  # Assuming your frontend runs on localhost:3000
    "https://example.com",    # Replace with your actual domain
]

# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of allowed origins
    allow_credentials=True,         # Allow cookies to be included in cross-origin requests
    allow_methods=["*"],            # Allow all methods
    allow_headers=["*"],            # Allow all headers
)

app.include_router(router)


# import os
# import subprocess
# import uuid
# from datetime import datetime
# from dotenv import load_dotenv
# from fastapi import FastAPI
# from sqlmodel import Session, SQLModel
# from .crud import crud
# from .config.database import engine
# from .schemas import schemas
#
# load_dotenv()
#
# app = FastAPI()
#
#
# def get_session():
#     with Session(engine) as session:
#         yield session
#
#
# @app.on_event("startup")
# def on_startup():
#     SQLModel.metadata.create_all(engine)
#
#
# @app.get("/")
# async def root():
#     return {"message": "Hello World"}
#
#
# @app.get("/hello/{name}")
# async def say_hello(name: str):
#     return {"message": f"Hello {name}"}
#

# @app.get("/scrape/amazon")
# async def scrape_reviews(amazon_url: str):
#     username = os.getenv("BRIGHT_DATA_USERNAME")
#     password = os.getenv("BRIGHT_DATA_PASSWORD")
#     host = os.getenv("BRIGHT_DATA_HOST")
#     port = 22225  # Ensure this is a string when constructing the proxy URL
#     session_id = randint(0, 1000000)
#     username = f"{username}-session-{session_id}"
#
#     # Proxies configuration
#     proxies = {
#         "http://": f"http://{username}-session-{session_id}:{password}@{host}:{port}",
#         "https://": f"https://{username}-session-{session_id}:{password}@{host}:{port}"
#     }
#
#     url = "https://www.httpbin.org/ip"
#     async with httpx.AsyncClient(proxies=proxies, verify=False) as client:
#         response = await client.get(url)
#         content = response.json()
#     return content


# @app.get("/scrape/amazon")
# async def scrape_amazon():
#     job_id = str(uuid.uuid4())
#     start_time = datetime.utcnow()
#     job = schemas.JobCreate(
#         url="https://www.amazon.com/Apple-iPhone-11-64GB-Unlocked/dp/B07ZPKZSSC",
#         status="started",
#         id=job_id,
#         start_time=start_time
#     )
#     crud.create_job(job)
#     amazon_url = "https://www.amazon.com/Apple-iPhone-11-64GB-Unlocked/dp/B07ZPKZSSC"
#     # Start Scrapy spider as a separate process
#     command = ["scrapy", "crawl", "amazon", "-a", f"url={amazon_url}", "-a", f"job_id={job_id}"]
#     # print current working directory
#     print(os.getcwd())
#     subprocess.Popen(command, cwd="scrapy-project")
#     return {"job_id": job_id, "status": "Scraping in progress..."}
#
#
# @app.get("/scrape/status/{job_id}")
# async def scrape_status(job_id: str):
#     job = crud.get_job(job_id)
#     return job
#
#
# # pull the job json from the request body and create a new job
# @app.put("/job/{job_id}")
# async def create_job(job_id: str, job: schemas.JobUpdate):
#     return crud.update_job(job_id, job)
#
#
# @app.get("/job/{job_id}")
# async def get_job(job_id: str):
#     return crud.get_job(job_id)
