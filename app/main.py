import os

from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .routes.route import router
from starlette.requests import Request
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
# Define a list of allowed origins for CORS
# It's better to specify the exact domains in a production environment
allowed_origins = [
    "http://localhost:3000",  # Assuming your frontend runs on localhost:3000
    "https://example.com",  # Replace with your actual domain
]

# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies to be included in cross-origin requests
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
app.add_middleware(
    SessionMiddleware,
    secret_key="secret",
)
oauth = OAuth()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id= CLIENT_ID,
    client_secret= CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
        "redirect_uri": "http://localhost:8000/auth"
    }
)

@router.get("/login")
async def login(request: Request):
    url = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, url)


@router.get("/auth")
async def auth(request: Request):
    try:
        pass
    except OAuthError as e:
        raise HTTPException(status_code=400, detail="OAuth error occurred")

app.include_router(router)
