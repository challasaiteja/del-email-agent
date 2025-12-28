"""Google OAuth2 authentication flow for Gmail API."""

import os
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import GOOGLE_CREDENTIALS_PATH, GMAIL_SCOPES


def get_gmail_auth_url() -> tuple[Flow, str]:
    """
    Generate the Gmail OAuth authorization URL.
    
    Returns:
        tuple: (Flow object, authorization URL)
    """
    if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"Google credentials file not found at {GOOGLE_CREDENTIALS_PATH}. "
            "Please download it from Google Cloud Console."
        )
    
    flow = Flow.from_client_secrets_file(
        GOOGLE_CREDENTIALS_PATH,
        scopes=GMAIL_SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"  # For desktop/local apps
    )
    
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    return flow, auth_url


def exchange_code_for_credentials(flow: Flow, auth_code: str) -> Credentials:
    """
    Exchange the authorization code for credentials.
    
    Args:
        flow: The OAuth flow object
        auth_code: The authorization code from the user
        
    Returns:
        Credentials object
    """
    flow.fetch_token(code=auth_code)
    return flow.credentials


def refresh_credentials(credentials: Credentials) -> Credentials:
    """
    Refresh expired credentials.
    
    Args:
        credentials: The credentials to refresh
        
    Returns:
        Refreshed credentials
    """
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials


def get_gmail_service(credentials: Credentials):
    """
    Build and return the Gmail API service.
    
    Args:
        credentials: Valid OAuth credentials
        
    Returns:
        Gmail API service object
    """
    return build("gmail", "v1", credentials=credentials)


def init_auth_state():
    """Initialize authentication state in Streamlit session."""
    if "credentials" not in st.session_state:
        st.session_state.credentials = None
    if "gmail_service" not in st.session_state:
        st.session_state.gmail_service = None
    if "auth_flow" not in st.session_state:
        st.session_state.auth_flow = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None


def is_authenticated() -> bool:
    """Check if user is authenticated with valid credentials."""
    if st.session_state.credentials is None:
        return False
    
    creds = st.session_state.credentials
    
    # Check if credentials are valid
    if creds.valid:
        return True
    
    # Try to refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds = refresh_credentials(creds)
            st.session_state.credentials = creds
            st.session_state.gmail_service = get_gmail_service(creds)
            return True
        except Exception:
            return False
    
    return False


def get_user_email() -> str | None:
    """Get the authenticated user's email address."""
    if st.session_state.gmail_service is None:
        return None
    
    try:
        profile = st.session_state.gmail_service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception:
        return None


def logout():
    """Clear authentication state."""
    st.session_state.credentials = None
    st.session_state.gmail_service = None
    st.session_state.auth_flow = None
    st.session_state.user_email = None

