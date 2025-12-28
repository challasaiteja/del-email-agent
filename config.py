"""Configuration settings for the Gmail Cleanup Agent."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# Google OAuth Configuration
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

# Email Filter Defaults
DEFAULT_DAYS_OLD = 30
MAX_EMAILS_PER_FETCH = 500

# App Configuration
APP_TITLE = "Gmail Cleanup Agent"
APP_ICON = "📧"

