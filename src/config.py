import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Jira Configuration
    jira_url: str = os.getenv("JIRA_URL", "")
    jira_username: str = os.getenv("JIRA_USERNAME", "")
    jira_token: str = os.getenv("JIRA_TOKEN", "")
    jira_webhook_secret: str = os.getenv("JIRA_WEBHOOK_SECRET", "")
    
    # GitHub Configuration
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")
    
    # Application Configuration
    app_name: str = os.getenv("APP_NAME", "todo-app")
    deployment_url_base: str = os.getenv("DEPLOYMENT_URL_BASE", "https://app.example.com")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()