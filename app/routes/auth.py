import os
from fastapi import APIRouter, HTTPException, Query, Request
import requests
from fastapi.responses import RedirectResponse
from core.git_client import GitClient

router = APIRouter()

@router.get("/auth/github/callback")
async def github_callback(request: Request, code: str = Query(...)):
    """Exchanges the temporary code for a GitHub access token."""
    token_url = "https://github.com/login/oauth/access_token"
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    headers = {"Accept": "application/json"}
    response = requests.post(token_url, data=data, headers=headers)
    token_data = response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to get access token.")

    access_token = token_data["access_token"]
    
    response = RedirectResponse(url=f"/?token={access_token}&platform=github", status_code=302)
    return response

@router.get("/auth/gitlab/callback")
async def gitlab_callback(request: Request, code: str = Query(...)):
    """Exchanges the temporary code for a GitLab access token."""
    token_url = "https://gitlab.com/oauth/token"
    client_id = os.getenv("GITLAB_CLIENT_ID")
    client_secret = os.getenv("GITLAB_CLIENT_SECRET")
    redirect_uri = os.getenv("GITLAB_REDIRECT_URI")

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    response = requests.post(token_url, data=data, headers={"Accept": "application/json"})
    token_data = response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail="Failed to get GitLab access token.")

    access_token = token_data["access_token"]
    
    response = RedirectResponse(url=f"/?token={access_token}&platform=gitlab", status_code=302)
    return response

@router.get("/repos")
async def get_repos(token: str, platform: str):
    """Fetches user repositories using the access token and platform."""
    try:
        client = GitClient(token, platform)
        repos = client.get_user_repos()
        return {"repos": repos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))