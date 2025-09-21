import os
import google.generativeai as genai

class LLMReviewer:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def review_code(self, file_content: str, file_path: str) -> str:
        prompt = f"""
You are an expert software developer and a senior code reviewer. Your task is to analyze the provided code for the entire repository. This code is from a repository focused on {file_path}.

Provide a single, comprehensive review of the entire codebase, focusing on overall architecture, common bugs, security vulnerabilities, and adherence to best practices. Highlight major issues and provide constructive, high-level feedback.

Finally, provide a code quality score from 1 to 10 at the end of your review.
Example: "Code Quality Score: 7/10"

Code to review:
{file_content}
"""
        response = self.model.generate_content(prompt)
        return response.text