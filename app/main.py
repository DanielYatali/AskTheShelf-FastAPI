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



