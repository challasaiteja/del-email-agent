"""In-memory action logging utility for tracking operations."""

from datetime import datetime
from enum import Enum
from typing import Any

import streamlit as st


class ActionType(Enum):
    """Types of actions that can be logged."""
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    FETCH_EMAILS = "fetch_emails"
    EMAILS_DELETED = "emails_deleted"
    AI_ANALYSIS = "ai_analysis"
    ERROR = "error"


class ActionLogger:
    """
    In-memory action logger that stores all operations in Streamlit session state.
    """
    
    @staticmethod
    def init():
        """Initialize the action log in session state."""
        if "action_log" not in st.session_state:
            st.session_state.action_log = []
    
    @staticmethod
    def log(
        action_type: ActionType,
        description: str,
        details: dict[str, Any] | None = None,
        status: str = "success",
    ):
        """
        Log an action to the session state.
        
        Args:
            action_type: The type of action
            description: Human-readable description
            details: Optional additional details
            status: success, warning, or error
        """
        ActionLogger.init()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type.value,
            "description": description,
            "details": details or {},
            "status": status,
        }
        
        st.session_state.action_log.append(entry)
    
    @staticmethod
    def get_logs(limit: int | None = None) -> list[dict]:
        """
        Get action logs, most recent first.
        
        Args:
            limit: Optional limit on number of logs to return
            
        Returns:
            List of log entries
        """
        ActionLogger.init()
        logs = list(reversed(st.session_state.action_log))
        
        if limit:
            return logs[:limit]
        return logs
    
    @staticmethod
    def get_logs_by_type(action_type: ActionType) -> list[dict]:
        """
        Get logs filtered by action type.
        
        Args:
            action_type: The type to filter by
            
        Returns:
            Filtered list of log entries
        """
        ActionLogger.init()
        return [
            log for log in st.session_state.action_log
            if log["type"] == action_type.value
        ]
    
    @staticmethod
    def get_deletion_stats() -> dict[str, Any]:
        """
        Get statistics about deleted emails in this session.
        
        Returns:
            Dictionary with deletion statistics
        """
        deletion_logs = ActionLogger.get_logs_by_type(ActionType.EMAILS_DELETED)
        
        total_deleted = sum(
            log.get("details", {}).get("count", 0)
            for log in deletion_logs
        )
        
        return {
            "total_deleted": total_deleted,
            "deletion_count": len(deletion_logs),
            "logs": deletion_logs,
        }
    
    @staticmethod
    def clear():
        """Clear all logs."""
        st.session_state.action_log = []
    
    @staticmethod
    def format_log_entry(entry: dict) -> str:
        """
        Format a log entry for display.
        
        Args:
            entry: Log entry dictionary
            
        Returns:
            Formatted string
        """
        timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
        status_emoji = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }.get(entry["status"], "ℹ️")
        
        return f"[{timestamp}] {status_emoji} {entry['description']}"


# Convenience functions for common logging operations
def log_auth_login(email: str):
    """Log a successful authentication."""
    ActionLogger.log(
        ActionType.AUTH_LOGIN,
        f"Authenticated as {email}",
        {"email": email},
    )


def log_auth_logout():
    """Log a logout."""
    ActionLogger.log(
        ActionType.AUTH_LOGOUT,
        "Logged out",
    )


def log_fetch_emails(count: int, query: str):
    """Log an email fetch operation."""
    ActionLogger.log(
        ActionType.FETCH_EMAILS,
        f"Fetched {count} emails",
        {"count": count, "query": query},
    )


def log_emails_deleted(count: int, success: int, failed: int):
    """Log email deletion."""
    status = "success" if failed == 0 else "warning"
    ActionLogger.log(
        ActionType.EMAILS_DELETED,
        f"Deleted {success} emails" + (f" ({failed} failed)" if failed else ""),
        {"count": count, "success": success, "failed": failed},
        status=status,
    )


def log_ai_analysis(analysis_type: str, result_summary: str):
    """Log AI analysis operation."""
    ActionLogger.log(
        ActionType.AI_ANALYSIS,
        f"AI {analysis_type}: {result_summary}",
        {"type": analysis_type, "summary": result_summary},
    )


def log_error(error_message: str, details: dict | None = None):
    """Log an error."""
    ActionLogger.log(
        ActionType.ERROR,
        f"Error: {error_message}",
        details,
        status="error",
    )

