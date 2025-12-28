"""Gmail API service for fetching and managing emails."""

import base64
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

import streamlit as st

from config import DEFAULT_DAYS_OLD, MAX_EMAILS_PER_FETCH


def build_search_query(
    days_old: int = DEFAULT_DAYS_OLD,
    sender_filter: str | None = None,
    subject_filter: str | None = None,
    label_filter: str | None = None,
    unread_only: bool = True,
) -> str:
    """
    Build a Gmail search query string.
    
    Args:
        days_old: Minimum age of emails in days
        sender_filter: Filter by sender email/name
        subject_filter: Filter by subject keywords
        label_filter: Filter by Gmail label
        unread_only: Only fetch unread emails
        
    Returns:
        Gmail search query string
    """
    query_parts = []
    
    # System labels that should be skipped (handled by other filters or use special syntax)
    system_labels_to_skip = {"UNREAD", "INBOX", "SENT", "DRAFT", "SPAM", "TRASH", "STARRED", "IMPORTANT"}
    
    # Age filter
    if days_old > 0:
        query_parts.append(f"older_than:{days_old}d")
    
    # Unread filter
    if unread_only:
        query_parts.append("is:unread")
    
    # Sender filter - wrap in quotes if contains spaces
    if sender_filter:
        if " " in sender_filter:
            query_parts.append(f'from:"{sender_filter}"')
        else:
            query_parts.append(f"from:{sender_filter}")
    
    # Subject filter - wrap in quotes if contains spaces
    if subject_filter:
        if " " in subject_filter:
            query_parts.append(f'subject:"{subject_filter}"')
        else:
            query_parts.append(f"subject:{subject_filter}")
    
    # Label filter - skip system labels that are handled differently
    if label_filter and label_filter != "All" and label_filter.upper() not in system_labels_to_skip:
        query_parts.append(f"label:{label_filter}")
    
    return " ".join(query_parts)


def fetch_emails(
    service,
    query: str,
    max_results: int = MAX_EMAILS_PER_FETCH,
) -> list[dict[str, Any]]:
    """
    Fetch emails matching the query.
    
    Args:
        service: Gmail API service object
        query: Gmail search query
        max_results: Maximum number of emails to fetch
        
    Returns:
        List of email dictionaries with metadata
    """
    emails = []
    
    try:
        # Get message IDs matching the query
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()
        
        messages = results.get("messages", [])
        
        if not messages:
            return []
        
        # Fetch details for each message
        for msg in messages:
            email_data = get_email_details(service, msg["id"])
            if email_data:
                emails.append(email_data)
        
        return emails
        
    except Exception as e:
        st.error(f"Error fetching emails: {str(e)}")
        return []


def get_email_details(service, message_id: str) -> dict[str, Any] | None:
    """
    Get detailed information for a single email.
    
    Args:
        service: Gmail API service object
        message_id: The email message ID
        
    Returns:
        Dictionary with email details or None if error
    """
    try:
        message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        
        headers = {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
        
        # Parse date
        date_str = headers.get("Date", "")
        try:
            date = parsedate_to_datetime(date_str)
        except Exception:
            date = datetime.now()
        
        # Calculate age in days
        age_days = (datetime.now(date.tzinfo) - date).days if date.tzinfo else (datetime.now() - date).days
        
        return {
            "id": message_id,
            "thread_id": message.get("threadId"),
            "from": headers.get("From", "Unknown"),
            "subject": headers.get("Subject", "(No Subject)"),
            "date": date.strftime("%Y-%m-%d %H:%M"),
            "age_days": age_days,
            "snippet": message.get("snippet", ""),
            "labels": message.get("labelIds", []),
            "size_estimate": message.get("sizeEstimate", 0),
        }
        
    except Exception as e:
        return None


def get_email_body(service, message_id: str) -> str:
    """
    Get the body content of an email.
    
    Args:
        service: Gmail API service object
        message_id: The email message ID
        
    Returns:
        Email body text
    """
    try:
        message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()
        
        payload = message.get("payload", {})
        
        # Try to get text/plain body
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        
        # Check parts for multipart messages
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8")
        
        return message.get("snippet", "")
        
    except Exception:
        return ""


def trash_emails(service, message_ids: list[str]) -> dict[str, Any]:
    """
    Move emails to trash.
    
    Args:
        service: Gmail API service object
        message_ids: List of message IDs to trash
        
    Returns:
        Dictionary with success count and errors
    """
    results = {
        "success": 0,
        "failed": 0,
        "errors": [],
    }
    
    for msg_id in message_ids:
        try:
            service.users().messages().trash(
                userId="me",
                id=msg_id,
            ).execute()
            results["success"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Failed to trash {msg_id}: {str(e)}")
    
    return results


def batch_trash_emails(service, message_ids: list[str]) -> dict[str, Any]:
    """
    Batch move emails to trash for better performance.
    
    Args:
        service: Gmail API service object
        message_ids: List of message IDs to trash
        
    Returns:
        Dictionary with results
    """
    if not message_ids:
        return {"success": 0, "failed": 0, "errors": []}
    
    try:
        # Use batchModify for efficiency
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": message_ids,
                "addLabelIds": ["TRASH"],
                "removeLabelIds": ["INBOX"],
            },
        ).execute()
        
        return {
            "success": len(message_ids),
            "failed": 0,
            "errors": [],
        }
        
    except Exception as e:
        # Fall back to individual trash if batch fails
        return trash_emails(service, message_ids)


def get_labels(service) -> list[dict[str, str]]:
    """
    Get all Gmail labels for the user.
    
    Args:
        service: Gmail API service object
        
    Returns:
        List of label dictionaries
    """
    try:
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        return [{"id": l["id"], "name": l["name"]} for l in labels]
    except Exception:
        return []


def get_sender_stats(emails: list[dict]) -> dict[str, int]:
    """
    Get statistics about email senders.
    
    Args:
        emails: List of email dictionaries
        
    Returns:
        Dictionary mapping sender to email count
    """
    sender_counts = {}
    for email in emails:
        sender = email.get("from", "Unknown")
        # Extract email address from "Name <email>" format
        if "<" in sender and ">" in sender:
            sender = sender[sender.find("<")+1:sender.find(">")]
        sender_counts[sender] = sender_counts.get(sender, 0) + 1
    
    # Sort by count descending
    return dict(sorted(sender_counts.items(), key=lambda x: x[1], reverse=True))

