import requests
import os
from github import Github
import gitlab
from atlassian import Bitbucket
from gitlab.exceptions import GitlabAuthenticationError

class GitClient:
    def __init__(self, token: str, platform: str):
        self.platform = platform
        self.token = token
        if self.platform == 'github':
            self.client = Github(self.token)
        elif self.platform == 'gitlab':
            self.client = gitlab.Gitlab('https://gitlab.com', oauth_token=self.token)
        elif self.platform == 'bitbucket':
            self.client = Bitbucket(
                url='https://bitbucket.org/',
                username=os.getenv("BITBUCKET_USERNAME"),
                password=os.getenv("BITBUCKET_APP_PASSWORD")
            )
        else:
            raise ValueError("Unsupported Git platform")

    def get_user_repos(self):
        try:
            if self.platform == 'github':
                return [repo.full_name for repo in self.client.get_user().get_repos()]
            elif self.platform == 'gitlab':
                projects = self.client.projects.list(get_all=True)
                return [project.path_with_namespace for project in projects]
            elif self.platform == 'bitbucket':
                return [repo['full_name'] for repo in self.client.get_user_repositories(username=os.getenv("BITBUCKET_USERNAME"))]
            return []
        except GitlabAuthenticationError:
            raise Exception("GitLab authentication failed. Please check your token and scopes.")
        except Exception as e:
            raise Exception(f"Failed to fetch repositories: {str(e)}")

    def get_repo_files(self, repo_name: str):
        try:
            files_to_review = {}
            file_extensions = (
                '.py', '.ipynb', '.js', '.ts', '.java', '.cpp', '.c', '.h', 
                '.html', '.css', '.scss', '.json', '.jsx', '.tsx', 
                '.go', '.rs', '.php', '.xml', '.yaml', '.yml'
            )
            
            if self.platform == 'github':
                repo = self.client.get_repo(repo_name)
                try:
                    contents = repo.get_contents("")
                except Exception as e:
                    if 'This repository is empty.' in str(e):
                        return {"error": "The selected repository is empty. Please choose a different one."}
                    raise

                directories_to_explore = [""]
                while directories_to_explore:
                    path = directories_to_explore.pop(0)
                    contents = repo.get_contents(path)
                    for content in contents:
                        if content.type == 'dir':
                            directories_to_explore.append(content.path)
                        elif content.type == 'file' and content.name.endswith(file_extensions):
                            file_content = requests.get(content.download_url).text
                            files_to_review[content.path] = file_content
            
            elif self.platform == 'gitlab':
                project = self.client.projects.get(repo_name)
                tree = project.repository_tree(recursive=True, all=True)
                for item in tree:
                    if item['type'] == 'blob' and item['name'].endswith(file_extensions):
                        file_content = project.files.get(file_path=item['path'], ref=project.default_branch).decode()
                        files_to_review[item['path']] = file_content

            elif self.platform == 'bitbucket':
                parts = repo_name.split('/')
                workspace = parts[0]
                repo_slug = parts[1]
                source = self.client.repositories.get_src(workspace=workspace, repo_slug=repo_slug)
                for path, file in source['files'].items():
                    if path.endswith(file_extensions):
                        file_content = requests.get(file['links']['self']['href']).text
                        files_to_review[path] = file_content

            return files_to_review
        except Exception as e:
            return {"error": str(e)}

    def post_comment(self, repo_name, pr_number, comment):
        """Posts a comment on a pull request, supporting multiple platforms."""
        if self.platform == 'github':
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
        elif self.platform == 'gitlab':
            project = self.client.projects.get(repo_name)
            pr = project.mergerequests.get(pr_number)
            pr.notes.create({'body': comment})