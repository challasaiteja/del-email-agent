"""Email list component with selection and display."""

import pandas as pd
import streamlit as st

from services.ai_service import analyze_email_for_importance


def init_selection_state():
    """Initialize email selection state."""
    if "selected_emails" not in st.session_state:
        st.session_state.selected_emails = set()


def render_email_table(emails: list[dict], sender_stats: dict[str, int]) -> list[str]:
    """
    Render the email table with selection checkboxes.
    
    Args:
        emails: List of email dictionaries
        sender_stats: Sender statistics for context
        
    Returns:
        List of selected email IDs
    """
    init_selection_state()
    
    if not emails:
        st.info("No emails found matching your filters.")
        return []
    
    # Create DataFrame for display
    df = pd.DataFrame(emails)
    
    # Add importance indicators
    df["indicators"] = df.apply(
        lambda row: get_importance_badge(row.to_dict()),
        axis=1
    )
    
    # Prepare display columns
    display_df = df[["from", "subject", "date", "age_days", "indicators"]].copy()
    display_df.columns = ["From", "Subject", "Date", "Age (days)", "Type"]
    
    # Truncate long values
    display_df["From"] = display_df["From"].apply(lambda x: x[:40] + "..." if len(str(x)) > 40 else x)
    display_df["Subject"] = display_df["Subject"].apply(lambda x: x[:50] + "..." if len(str(x)) > 50 else x)
    
    # Selection header
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Select All", key="select_all_btn"):
            st.session_state.selected_emails = {e["id"] for e in emails}
            st.rerun()
    
    with col2:
        if st.button("Clear Selection", key="clear_selection_btn"):
            st.session_state.selected_emails = set()
            st.rerun()
    
    with col3:
        st.write(f"**{len(st.session_state.selected_emails)}** of {len(emails)} selected")
    
    st.divider()
    
    # Render emails with checkboxes
    for idx, email in enumerate(emails):
        email_id = email["id"]
        is_selected = email_id in st.session_state.selected_emails
        
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            if st.checkbox(
                "",
                value=is_selected,
                key=f"email_cb_{email_id}",
                label_visibility="collapsed",
            ):
                st.session_state.selected_emails.add(email_id)
            else:
                st.session_state.selected_emails.discard(email_id)
        
        with col2:
            render_email_card(email, is_selected)
        
        # Show first 50 emails, then offer to load more
        if idx >= 49:
            remaining = len(emails) - 50
            if remaining > 0:
                st.info(f"Showing first 50 emails. {remaining} more available.")
            break
    
    return list(st.session_state.selected_emails)


def render_email_card(email: dict, is_selected: bool = False):
    """
    Render a single email as a card.
    
    Args:
        email: Email dictionary
        is_selected: Whether email is selected
    """
    # Get importance badge
    badge = get_importance_badge(email)
    
    # Style based on selection
    bg_color = "#1e3a5f" if is_selected else "#0e1117"
    border_color = "#4a9eff" if is_selected else "#333"
    
    # Truncate values
    sender = email.get("from", "Unknown")
    sender_display = sender[:50] + "..." if len(sender) > 50 else sender
    subject = email.get("subject", "(No Subject)")
    subject_display = subject[:70] + "..." if len(subject) > 70 else subject
    snippet = email.get("snippet", "")[:100]
    
    st.markdown(
        f"""
        <div style="
            background: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold; color: #fff;">{sender_display}</span>
                <span style="color: #888; font-size: 0.85em;">{email.get("date", "")} ({email.get("age_days", 0)}d ago)</span>
            </div>
            <div style="margin-top: 4px;">
                <span style="color: #ddd;">{subject_display}</span>
                {badge}
            </div>
            <div style="color: #888; font-size: 0.85em; margin-top: 4px;">
                {snippet}...
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_importance_badge(email: dict) -> str:
    """
    Get an HTML badge indicating email type.
    
    Args:
        email: Email dictionary
        
    Returns:
        HTML string for badge
    """
    analysis = analyze_email_for_importance(email)
    
    badges = []
    
    if analysis.get("likely_newsletter"):
        badges.append('<span style="background: #2d5a27; color: #98d895; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; margin-left: 8px;">Newsletter</span>')
    
    if analysis.get("likely_promotional"):
        badges.append('<span style="background: #5a4327; color: #d8c595; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; margin-left: 8px;">Promo</span>')
    
    if analysis.get("likely_automated"):
        badges.append('<span style="background: #3d3d5c; color: #a8a8d8; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; margin-left: 8px;">Auto</span>')
    
    if analysis.get("potentially_important"):
        badges.append('<span style="background: #5c3d3d; color: #d8a8a8; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; margin-left: 8px;">⚠️ Review</span>')
    
    return " ".join(badges)


def render_sender_breakdown(sender_stats: dict[str, int], on_select_sender: callable):
    """
    Render a breakdown of emails by sender with bulk select options.
    
    Args:
        sender_stats: Dictionary mapping sender to count
        on_select_sender: Callback when sender is selected for bulk action
    """
    st.subheader("📬 Emails by Sender")
    
    if not sender_stats:
        st.info("No sender data available.")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {"Sender": sender, "Count": count}
        for sender, count in sender_stats.items()
    ])
    
    # Show top 20
    df_display = df.head(20)
    
    for _, row in df_display.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            sender = row["Sender"]
            display_sender = sender[:40] + "..." if len(sender) > 40 else sender
            st.text(display_sender)
        
        with col2:
            st.text(f"{row['Count']} emails")
        
        with col3:
            if st.button("Select All", key=f"select_sender_{sender[:20]}"):
                on_select_sender(sender)

