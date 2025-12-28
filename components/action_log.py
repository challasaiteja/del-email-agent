"""Action log display component."""

import streamlit as st

from utils.logger import ActionLogger, ActionType


def render_action_log(max_entries: int = 50):
    """
    Render the action log panel.
    
    Args:
        max_entries: Maximum number of log entries to display
    """
    st.subheader("📜 Action Log")
    
    logs = ActionLogger.get_logs(limit=max_entries)
    
    if not logs:
        st.info("No actions logged yet. Actions will appear here as you use the app.")
        return
    
    # Summary stats
    stats = ActionLogger.get_deletion_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Actions", len(logs))
    
    with col2:
        st.metric("Emails Deleted", stats["total_deleted"])
    
    with col3:
        st.metric("Delete Operations", stats["deletion_count"])
    
    st.divider()
    
    # Log entries
    for entry in logs:
        render_log_entry(entry)
    
    # Clear button
    st.divider()
    if st.button("Clear Log", type="secondary"):
        ActionLogger.clear()
        st.rerun()


def render_log_entry(entry: dict):
    """
    Render a single log entry.
    
    Args:
        entry: Log entry dictionary
    """
    from datetime import datetime
    
    # Parse timestamp
    try:
        timestamp = datetime.fromisoformat(entry["timestamp"])
        time_str = timestamp.strftime("%H:%M:%S")
    except Exception:
        time_str = "??:??:??"
    
    # Status styling
    status = entry.get("status", "success")
    status_colors = {
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545",
    }
    status_icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    
    color = status_colors.get(status, "#6c757d")
    icon = status_icons.get(status, "ℹ️")
    
    # Action type badge
    action_type = entry.get("type", "unknown")
    type_colors = {
        ActionType.AUTH_LOGIN.value: "#17a2b8",
        ActionType.AUTH_LOGOUT.value: "#6c757d",
        ActionType.FETCH_EMAILS.value: "#007bff",
        ActionType.FILTER_APPLIED.value: "#6610f2",
        ActionType.EMAILS_SELECTED.value: "#fd7e14",
        ActionType.EMAILS_DELETED.value: "#dc3545",
        ActionType.AI_ANALYSIS.value: "#20c997",
        ActionType.ERROR.value: "#dc3545",
    }
    type_color = type_colors.get(action_type, "#6c757d")
    
    # Render
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            padding: 8px 12px;
            margin-bottom: 4px;
            background: #1a1a2e;
            border-radius: 6px;
            border-left: 3px solid {color};
        ">
            <span style="color: #888; font-size: 0.8em; min-width: 70px;">{time_str}</span>
            <span style="margin-left: 8px;">{icon}</span>
            <span style="
                background: {type_color};
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.75em;
                margin-left: 8px;
                text-transform: uppercase;
            ">{action_type.replace('_', ' ')}</span>
            <span style="margin-left: 12px; color: #ddd;">{entry.get('description', '')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Show details in expander if available
    details = entry.get("details", {})
    if details and len(details) > 0:
        with st.expander("Details", expanded=False):
            for key, value in details.items():
                st.text(f"{key}: {value}")


def render_compact_log(max_entries: int = 5):
    """
    Render a compact version of the action log for the sidebar.
    
    Args:
        max_entries: Maximum entries to show
    """
    logs = ActionLogger.get_logs(limit=max_entries)
    
    if not logs:
        st.caption("No recent actions")
        return
    
    for entry in logs:
        formatted = ActionLogger.format_log_entry(entry)
        st.caption(formatted)

