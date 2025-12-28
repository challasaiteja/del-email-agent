"""Sidebar component with filter controls."""

import streamlit as st

from config import DEFAULT_DAYS_OLD


def render_sidebar_filters(labels: list[dict] | None = None) -> dict:
    """
    Render the sidebar with filter controls.
    
    Args:
        labels: Optional list of Gmail labels
        
    Returns:
        Dictionary with current filter values
    """
    st.sidebar.header("📋 Filters")
    
    # Days old filter
    days_old = st.sidebar.slider(
        "Minimum age (days)",
        min_value=1,
        max_value=365,
        value=DEFAULT_DAYS_OLD,
        help="Only show emails older than this many days",
    )
    
    # Unread only toggle
    unread_only = st.sidebar.checkbox(
        "Unread only",
        value=True,
        help="Only show unread emails",
    )
    
    # Sender filter
    sender_filter = st.sidebar.text_input(
        "Filter by sender",
        placeholder="e.g., newsletter@example.com",
        help="Filter emails from a specific sender",
    )
    
    # Subject filter
    subject_filter = st.sidebar.text_input(
        "Filter by subject",
        placeholder="e.g., weekly digest",
        help="Filter emails containing keywords in subject",
    )
    
    # Label filter - exclude system labels that don't work with label: syntax
    system_labels = {"UNREAD", "INBOX", "SENT", "DRAFT", "SPAM", "TRASH", "STARRED", 
                     "IMPORTANT", "CHAT", "CATEGORY_PERSONAL", "CATEGORY_SOCIAL",
                     "CATEGORY_PROMOTIONS", "CATEGORY_UPDATES", "CATEGORY_FORUMS"}
    user_labels = [l["name"] for l in (labels or []) if l["name"] not in system_labels]
    label_options = ["All"] + user_labels
    label_filter = st.sidebar.selectbox(
        "Filter by label",
        options=label_options,
        index=0,
        help="Filter by custom Gmail labels (system labels are excluded)",
    )
    
    st.sidebar.divider()
    
    # Quick filter presets
    st.sidebar.subheader("🚀 Quick Filters")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Newsletters", use_container_width=True):
            st.session_state.quick_filter = "newsletter"
    
    with col2:
        if st.button("Promotions", use_container_width=True):
            st.session_state.quick_filter = "promotions"
    
    col3, col4 = st.sidebar.columns(2)
    
    with col3:
        if st.button("Social", use_container_width=True):
            st.session_state.quick_filter = "social"
    
    with col4:
        if st.button("90+ Days", use_container_width=True):
            st.session_state.quick_filter = "very_old"
    
    # Apply quick filter if set
    quick_filter = st.session_state.get("quick_filter")
    if quick_filter == "newsletter":
        subject_filter = "newsletter OR digest OR weekly"
    elif quick_filter == "promotions":
        subject_filter = "sale OR discount OR offer OR deal"
    elif quick_filter == "social":
        sender_filter = "linkedin OR twitter OR facebook OR instagram"
    elif quick_filter == "very_old":
        days_old = 90
    
    # Clear quick filter after applying
    if quick_filter:
        st.session_state.quick_filter = None
    
    filters = {
        "days_old": days_old,
        "unread_only": unread_only,
        "sender_filter": sender_filter.strip() if sender_filter else None,
        "subject_filter": subject_filter.strip() if subject_filter else None,
        "label_filter": label_filter if label_filter != "All" else None,
    }
    
    return filters


def render_sidebar_stats(emails: list[dict], sender_stats: dict[str, int]):
    """
    Render email statistics in the sidebar.
    
    Args:
        emails: List of fetched emails
        sender_stats: Sender statistics dictionary
    """
    st.sidebar.divider()
    st.sidebar.header("📊 Statistics")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.sidebar.metric("Total Emails", len(emails))
    
    with col2:
        st.sidebar.metric("Unique Senders", len(sender_stats))
    
    # Top senders
    if sender_stats:
        st.sidebar.subheader("Top Senders")
        top_5 = list(sender_stats.items())[:5]
        for sender, count in top_5:
            # Truncate long sender names
            display_sender = sender[:25] + "..." if len(sender) > 25 else sender
            st.sidebar.text(f"{display_sender}: {count}")



