import os
import requests
from fastapi import APIRouter, Header, HTTPException, Request
from core.git_client import GitClient
from core.llm_reviewer import LLMReviewer

router = APIRouter()

@router.post("/github-webhook")
async def handle_github_webhook(request: Request, x_github_event: str = Header(...)):
    # In a real app, you would verify the signature to ensure it's from GitHub
    payload = await request.json()
    if x_github_event == "pull_request" and payload['action'] in ['opened', 'reopened', 'synchronize']:
        pr_data = payload['pull_request']
        repo_name = pr_data['head']['repo']['full_name']
        
        token = os.getenv("GITHUB_TOKEN") 
        if not token:
            raise HTTPException(status_code=401, detail="No GitHub token configured")

        git_client = GitClient(token, 'github')
        llm_reviewer = LLMReviewer()

        files_to_review = git_client.get_repo_files(repo_name)

        if "error" in files_to_review:
            raise HTTPException(status_code=400, detail=files_to_review["error"])

        combined_code = ""
        for file_path, file_content in files_to_review.items():
            combined_code += f"--- START OF FILE: {file_path} ---\n{file_content}\n--- END OF FILE: {file_path} ---\n\n"

        if not combined_code:
            return {"message": "No code files found to review.", "status": "success"}

        overall_review_result = llm_reviewer.review_code(combined_code, f"Pull Request in {repo_name}")

        pr_number = pr_data['number']
        try:
            print(f"Review for PR #{pr_number} in {repo_name}:\n{overall_review_result}")
        except Exception as e:
            return {"message": f"Webhook review successful, but failed to post comment: {e}", "status": "partial_success"}

    return {"message": "Webhook received and review process initiated", "status": "success"}