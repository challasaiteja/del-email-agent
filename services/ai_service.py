"""AI service for email analysis and recommendations using OpenAI."""

import json
from typing import Any

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL


def get_openai_client() -> OpenAI | None:
    """Get OpenAI client if API key is configured."""
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def categorize_senders(sender_stats: dict[str, int]) -> dict[str, list[str]]:
    """
    Categorize email senders into groups using AI.
    
    Args:
        sender_stats: Dictionary mapping sender email to count
        
    Returns:
        Dictionary with categories as keys and list of senders as values
    """
    client = get_openai_client()
    if not client or not sender_stats:
        return {"uncategorized": list(sender_stats.keys())}
    
    # Take top 50 senders for analysis
    top_senders = list(sender_stats.keys())[:50]
    
    prompt = f"""Analyze these email senders and categorize them into groups.
    
Senders:
{json.dumps(top_senders, indent=2)}

Categorize into these groups:
- newsletter: Regular newsletters and subscriptions
- promotional: Marketing, sales, deals, promotions
- social: Social media notifications (LinkedIn, Twitter, Facebook, etc.)
- automated: System notifications, alerts, no-reply addresses
- potentially_important: Might be from real people or important services

Return a JSON object with category names as keys and arrays of sender emails as values.
Only include senders in one category. Return ONLY valid JSON, no other text."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {"uncategorized": top_senders}


def generate_deletion_summary(emails: list[dict], sender_stats: dict[str, int]) -> str:
    """
    Generate a human-readable summary of what will be deleted.
    
    Args:
        emails: List of email dictionaries
        sender_stats: Dictionary mapping sender to count
        
    Returns:
        Summary string
    """
    client = get_openai_client()
    
    if not client:
        # Fallback to basic summary
        return _basic_summary(emails, sender_stats)
    
    # Prepare data for AI
    top_senders = list(sender_stats.items())[:10]
    total_emails = len(emails)
    
    prompt = f"""Create a brief, friendly summary of emails about to be deleted.

Total emails: {total_emails}
Top senders (sender: count):
{json.dumps(top_senders, indent=2)}

Write 2-3 sentences summarizing:
1. How many emails will be deleted
2. Main sources (group similar senders)
3. Any recommendation (e.g., if many are from newsletters, suggest unsubscribing)

Keep it concise and helpful."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception:
        return _basic_summary(emails, sender_stats)


def _basic_summary(emails: list[dict], sender_stats: dict[str, int]) -> str:
    """Generate a basic summary without AI."""
    total = len(emails)
    unique_senders = len(sender_stats)
    top_sender = list(sender_stats.keys())[0] if sender_stats else "Unknown"
    top_count = list(sender_stats.values())[0] if sender_stats else 0
    
    return (
        f"Ready to delete {total} unread emails from {unique_senders} senders. "
        f"Top sender: {top_sender} ({top_count} emails)."
    )


def get_smart_recommendations(
    emails: list[dict],
    sender_stats: dict[str, int],
    categories: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """
    Generate smart recommendations for email cleanup.
    
    Args:
        emails: List of email dictionaries
        sender_stats: Dictionary mapping sender to count
        categories: Optional pre-computed sender categories
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Find high-volume senders
    high_volume_threshold = 10
    high_volume_senders = [
        sender for sender, count in sender_stats.items()
        if count >= high_volume_threshold
    ]
    
    if high_volume_senders:
        recommendations.append({
            "type": "bulk_delete",
            "title": "High-Volume Senders",
            "description": f"Found {len(high_volume_senders)} senders with 10+ unread emails each.",
            "senders": high_volume_senders[:5],
            "action": "Consider deleting all emails from these senders",
            "priority": "high",
        })
    
    # Category-based recommendations
    if categories:
        for category, senders in categories.items():
            if category in ["newsletter", "promotional"] and senders:
                category_emails = sum(
                    sender_stats.get(s, 0) for s in senders
                    if s in sender_stats
                )
                if category_emails > 0:
                    recommendations.append({
                        "type": "category_delete",
                        "title": f"{category.title()} Emails",
                        "description": f"Found {category_emails} emails from {category} sources.",
                        "senders": senders[:5],
                        "action": f"Delete all {category} emails",
                        "priority": "medium",
                    })
    
    # Find old emails
    very_old_emails = [e for e in emails if e.get("age_days", 0) > 90]
    if very_old_emails:
        recommendations.append({
            "type": "old_emails",
            "title": "Very Old Emails (90+ days)",
            "description": f"Found {len(very_old_emails)} emails older than 90 days.",
            "action": "Delete all emails older than 90 days",
            "priority": "medium",
        })
    
    return recommendations


def analyze_email_for_importance(email: dict) -> dict[str, Any]:
    """
    Analyze a single email for importance indicators.
    
    Args:
        email: Email dictionary
        
    Returns:
        Analysis dictionary
    """
    sender = email.get("from", "").lower()
    subject = email.get("subject", "").lower()
    
    # Simple heuristics (can be enhanced with AI)
    importance_signals = {
        "likely_automated": any(x in sender for x in ["noreply", "no-reply", "donotreply", "notification"]),
        "likely_newsletter": any(x in subject for x in ["newsletter", "digest", "weekly", "monthly", "unsubscribe"]),
        "likely_promotional": any(x in subject for x in ["sale", "off", "deal", "discount", "offer", "free"]),
        "potentially_important": any(x in subject for x in ["invoice", "receipt", "confirm", "action required"]),
    }
    
    return importance_signals

