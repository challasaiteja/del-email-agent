"""
Gmail Cleanup Agent - Main Streamlit Application

A smart email cleanup tool that helps you delete old unread emails
with AI-powered recommendations and filtering.
"""

import streamlit as st

from config import APP_TITLE, APP_ICON
from auth.gmail_auth import (
    init_auth_state,
    is_authenticated,
    get_gmail_auth_url,
    exchange_code_for_credentials,
    get_gmail_service,
    get_user_email,
    logout,
)
from services.gmail_service import (
    build_search_query,
    fetch_emails,
    get_labels,
    get_sender_stats,
    batch_trash_emails,
)
from services.ai_service import (
    categorize_senders,
    generate_deletion_summary,
    get_smart_recommendations,
)
from components.sidebar import render_sidebar_filters, render_sidebar_stats
from components.email_list import render_email_table, render_sender_breakdown
from components.action_log import render_action_log, render_compact_log
from utils.logger import (
    ActionLogger,
    log_auth_login,
    log_auth_logout,
    log_fetch_emails,
    log_emails_deleted,
    log_ai_analysis,
    log_error,
)


# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1a2e 100%);
    }
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stats-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #333;
    }
    .recommendation-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #4a9eff;
        margin-bottom: 12px;
    }
    div[data-testid="stSidebar"] {
        background: #0e1117;
    }
</style>
""", unsafe_allow_html=True)


def init_app_state():
    """Initialize all application state."""
    init_auth_state()
    ActionLogger.init()
    
    if "emails" not in st.session_state:
        st.session_state.emails = []
    if "sender_stats" not in st.session_state:
        st.session_state.sender_stats = {}
    if "labels" not in st.session_state:
        st.session_state.labels = []
    if "categories" not in st.session_state:
        st.session_state.categories = None
    if "last_query" not in st.session_state:
        st.session_state.last_query = None


def render_auth_page():
    """Render the authentication page."""
    st.markdown('<h1 class="main-header">📧 Gmail Cleanup Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligently clean up your inbox by removing old unread emails</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### Welcome! 👋
        
        This tool helps you:
        - 🔍 Find old unread emails (30+ days)
        - 🤖 Get AI-powered cleanup recommendations
        - 🗑️ Safely delete emails (moves to Trash)
        - 📊 Track all your actions
        
        ---
        
        ### Connect Your Gmail Account
        """)
        
        try:
            # Generate auth URL
            flow, auth_url = get_gmail_auth_url()
            st.session_state.auth_flow = flow
            
            st.markdown(f"**Step 1:** Click the button below to authorize access:")
            st.link_button("🔐 Authorize Gmail Access", auth_url, use_container_width=True)
            
            st.markdown("**Step 2:** After authorizing, paste the code below:")
            
            auth_code = st.text_input(
                "Authorization Code",
                type="password",
                placeholder="Paste your authorization code here",
            )
            
            if st.button("Connect", type="primary", use_container_width=True):
                if auth_code:
                    try:
                        credentials = exchange_code_for_credentials(
                            st.session_state.auth_flow,
                            auth_code.strip(),
                        )
                        st.session_state.credentials = credentials
                        st.session_state.gmail_service = get_gmail_service(credentials)
                        
                        # Get user email
                        user_email = get_user_email()
                        st.session_state.user_email = user_email
                        
                        # Log the action
                        log_auth_login(user_email or "Unknown")
                        
                        st.success(f"Connected as {user_email}!")
                        st.rerun()
                        
                    except Exception as e:
                        log_error(f"Authentication failed: {str(e)}")
                        st.error(f"Authentication failed: {str(e)}")
                else:
                    st.warning("Please enter the authorization code.")
                    
        except FileNotFoundError as e:
            st.error(str(e))
            st.info("""
            **Setup Instructions:**
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select existing
            3. Enable the Gmail API
            4. Create OAuth 2.0 credentials (Desktop app)
            5. Download the credentials and save as `credentials.json` in the app directory
            """)


def render_main_dashboard():
    """Render the main email dashboard."""
    # Header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<h1 class="main-header">📧 Gmail Cleanup Agent</h1>', unsafe_allow_html=True)
        st.caption(f"Connected as: {st.session_state.user_email}")
    
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            log_auth_logout()
            logout()
            st.session_state.emails = []
            st.session_state.sender_stats = {}
            st.rerun()
    
    # Fetch labels if not already done
    if not st.session_state.labels:
        st.session_state.labels = get_labels(st.session_state.gmail_service)
    
    # Sidebar filters
    filters = render_sidebar_filters(st.session_state.labels)
    
    # Fetch button
    st.sidebar.divider()
    if st.sidebar.button("🔍 Fetch Emails", type="primary", use_container_width=True):
        fetch_and_analyze_emails(filters)
    
    # Sidebar stats
    if st.session_state.emails:
        render_sidebar_stats(st.session_state.emails, st.session_state.sender_stats)
    
    # Sidebar recent actions
    st.sidebar.divider()
    st.sidebar.subheader("📜 Recent Actions")
    render_compact_log(5)
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📬 Emails", "💡 Recommendations", "📜 Action Log"])
    
    with tab1:
        render_emails_tab()
    
    with tab2:
        render_recommendations_tab()
    
    with tab3:
        render_action_log()


def fetch_and_analyze_emails(filters: dict):
    """Fetch emails based on filters and analyze them."""
    with st.spinner("Fetching emails..."):
        query = build_search_query(
            days_old=filters["days_old"],
            sender_filter=filters["sender_filter"],
            subject_filter=filters["subject_filter"],
            label_filter=filters["label_filter"],
            unread_only=filters["unread_only"],
        )
        
        # Store query for display
        st.session_state.last_query = query
        
        emails = fetch_emails(st.session_state.gmail_service, query)
        st.session_state.emails = emails
        st.session_state.selected_emails = set()
        
        # Log the fetch
        log_fetch_emails(len(emails), query)
        
        if emails:
            # Calculate sender stats
            st.session_state.sender_stats = get_sender_stats(emails)
            
            # AI categorization (if OpenAI is configured)
            with st.spinner("Analyzing emails with AI..."):
                try:
                    categories = categorize_senders(st.session_state.sender_stats)
                    st.session_state.categories = categories
                    log_ai_analysis("categorization", f"Categorized {len(st.session_state.sender_stats)} senders")
                except Exception as e:
                    st.session_state.categories = None
            
            st.success(f"Found {len(emails)} emails matching your filters!")
        else:
            st.session_state.sender_stats = {}
            st.session_state.categories = None
            st.info(f"No emails found matching your filters.")
            st.caption(f"Query used: `{query}`")


def render_emails_tab():
    """Render the emails tab content."""
    emails = st.session_state.emails
    
    if not emails:
        st.info("👆 Use the filters in the sidebar and click 'Fetch Emails' to get started.")
        return
    
    # Summary
    summary = generate_deletion_summary(emails, st.session_state.sender_stats)
    st.markdown(f"""
    <div class="stats-card">
        <h4>📊 Summary</h4>
        <p>{summary}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Email list with selection
    selected_ids = render_email_table(emails, st.session_state.sender_stats)
    
    # Delete button
    if selected_ids:
        st.divider()
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button(
                f"🗑️ Delete {len(selected_ids)} Emails",
                type="primary",
                use_container_width=True,
            ):
                delete_selected_emails(selected_ids)


def delete_selected_emails(email_ids: list[str]):
    """Delete the selected emails."""
    with st.spinner(f"Moving {len(email_ids)} emails to trash..."):
        result = batch_trash_emails(st.session_state.gmail_service, email_ids)
        
        # Log the deletion
        log_emails_deleted(
            len(email_ids),
            result["success"],
            result["failed"],
        )
        
        if result["success"] > 0:
            st.success(f"✅ Successfully moved {result['success']} emails to trash!")
            
            # Remove deleted emails from state
            deleted_set = set(email_ids)
            st.session_state.emails = [
                e for e in st.session_state.emails
                if e["id"] not in deleted_set
            ]
            st.session_state.selected_emails = set()
            
            # Update sender stats
            st.session_state.sender_stats = get_sender_stats(st.session_state.emails)
        
        if result["failed"] > 0:
            st.warning(f"⚠️ Failed to delete {result['failed']} emails.")
            for error in result["errors"][:5]:
                st.error(error)


def render_recommendations_tab():
    """Render the AI recommendations tab."""
    st.subheader("💡 Smart Recommendations")
    
    if not st.session_state.emails:
        st.info("Fetch emails first to get AI-powered recommendations.")
        return
    
    recommendations = get_smart_recommendations(
        st.session_state.emails,
        st.session_state.sender_stats,
        st.session_state.categories,
    )
    
    if not recommendations:
        st.success("✨ Your inbox looks good! No specific recommendations at this time.")
        return
    
    for rec in recommendations:
        render_recommendation_card(rec)
    
    # Sender breakdown
    st.divider()
    
    def on_select_sender(sender: str):
        """Select all emails from a specific sender."""
        matching_ids = {
            e["id"] for e in st.session_state.emails
            if sender in e.get("from", "")
        }
        st.session_state.selected_emails.update(matching_ids)
        st.rerun()
    
    render_sender_breakdown(st.session_state.sender_stats, on_select_sender)


def render_recommendation_card(rec: dict):
    """Render a recommendation card."""
    priority_colors = {
        "high": "#dc3545",
        "medium": "#ffc107",
        "low": "#28a745",
    }
    priority = rec.get("priority", "medium")
    color = priority_colors.get(priority, "#6c757d")
    
    senders = rec.get("senders", [])
    senders_text = ", ".join(s[:30] for s in senders[:3])
    if len(senders) > 3:
        senders_text += f" +{len(senders) - 3} more"
    
    st.markdown(f"""
    <div class="recommendation-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; color: #fff;">{rec.get('title', 'Recommendation')}</h4>
            <span style="
                background: {color};
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                text-transform: uppercase;
            ">{priority}</span>
        </div>
        <p style="color: #bbb; margin: 8px 0;">{rec.get('description', '')}</p>
        <p style="color: #888; font-size: 0.9em;">📧 {senders_text}</p>
        <p style="color: #4a9eff; font-weight: 500;">{rec.get('action', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action button
    if rec.get("senders"):
        if st.button(f"Select {rec['title']}", key=f"rec_{rec['title'][:20]}"):
            # Select emails from these senders
            matching_ids = set()
            for email in st.session_state.emails:
                sender = email.get("from", "")
                for rec_sender in rec["senders"]:
                    if rec_sender in sender:
                        matching_ids.add(email["id"])
                        break
            
            st.session_state.selected_emails.update(matching_ids)
            st.success(f"Selected {len(matching_ids)} emails!")
            st.rerun()


def main():
    """Main application entry point."""
    init_app_state()
    
    if is_authenticated():
        render_main_dashboard()
    else:
        render_auth_page()


if __name__ == "__main__":
    main()

