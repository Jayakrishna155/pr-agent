import re
from fastapi import APIRouter, HTTPException
from core.llm_reviewer import LLMReviewer
from core.git_client import GitClient
from pydantic import BaseModel
from google.api_core.exceptions import InvalidArgument

router = APIRouter()

class ReviewRequest(BaseModel):
    repo_name: str
    token: str
    platform: str

@router.post("/review")
async def review_repo(request: ReviewRequest):
    try:
        git_client = GitClient(request.token, request.platform)
        llm_reviewer = LLMReviewer()

        files_to_review = git_client.get_repo_files(request.repo_name)
        if "error" in files_to_review:
            raise HTTPException(status_code=400, detail=files_to_review["error"])

        # Consolidate all file content into a single string for one comprehensive review
        combined_code = ""
        for file_path, file_content in files_to_review.items():
            combined_code += f"--- START OF FILE: {file_path} ---\n{file_content}\n--- END OF FILE: {file_path} ---\n\n"

        if not combined_code:
            return {"overall_review": "No code files found to review."}

        try:
            overall_review_result = llm_reviewer.review_code(combined_code, f"Overall Repository - {request.platform}")
        except InvalidArgument as e:
            error_message = "The repository is too large for the LLM's context window. Please choose a smaller repository."
            raise HTTPException(status_code=400, detail=error_message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during the AI review: {str(e)}")
        
        score_match = re.search(r"Code Quality Score: (\d+)/10", overall_review_result)
        score = int(score_match.group(1)) if score_match else None

        return {
            "overall_review": overall_review_result,
            "score": score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))