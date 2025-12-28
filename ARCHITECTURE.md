# Gmail Cleanup Agent - Technical Documentation

## Overview

The Gmail Cleanup Agent is a Python-based web application that helps users delete old unread emails from their Gmail inbox. It provides smart filtering, AI-powered recommendations, and a safe deletion workflow.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Streamlit | Interactive web UI with widgets |
| **Backend** | Python 3.10+ | Core application logic |
| **Authentication** | Google OAuth 2.0 | Secure Gmail access |
| **Gmail API** | google-api-python-client | Email operations (fetch, delete) |
| **AI** | OpenAI GPT-4o-mini | Email categorization & summaries |
| **State Management** | Streamlit Session State | In-memory user session data |

### Dependencies

```
streamlit>=1.28.0          # Web framework
google-auth-oauthlib>=1.1.0 # OAuth 2.0 flow
google-api-python-client>=2.100.0  # Gmail API client
openai>=1.0.0              # AI recommendations
python-dotenv>=1.0.0       # Environment variables
pandas>=2.0.0              # Data manipulation
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Sidebar    │  │  Email List  │  │  Recommendations     │   │
│  │  (Filters)   │  │  (Selection) │  │  (AI Suggestions)    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APP.PY (Controller)                         │
│  • Route between auth/dashboard views                            │
│  • Orchestrate fetch → analyze → display → delete flow           │
│  • Manage session state                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  AUTH MODULE  │    │ GMAIL SERVICE │    │  AI SERVICE   │
│               │    │               │    │               │
│ • OAuth flow  │    │ • Build query │    │ • Categorize  │
│ • Token mgmt  │    │ • Fetch emails│    │   senders     │
│ • User profile│    │ • Trash emails│    │ • Summarize   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Google OAuth  │    │   Gmail API   │    │  OpenAI API   │
│   Servers     │    │   Servers     │    │   Servers     │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Project Structure

```
gmail-cleanup-agent/
├── app.py                     # Main entry point & controller
├── config.py                  # Configuration constants
│
├── auth/
│   ├── __init__.py
│   └── gmail_auth.py          # OAuth 2.0 authentication
│
├── services/
│   ├── __init__.py
│   ├── gmail_service.py       # Gmail API operations
│   └── ai_service.py          # OpenAI integration
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py             # Filter controls UI
│   ├── email_list.py          # Email display & selection
│   └── action_log.py          # Activity history
│
├── utils/
│   ├── __init__.py
│   └── logger.py              # Action logging utility
│
├── credentials.json           # Google OAuth credentials (gitignored)
├── .env                       # Environment variables (gitignored)
├── requirements.txt
└── README.md
```

---

## Core Logic Flow

### 1. Authentication Flow

```
User clicks "Connect Gmail"
        │
        ▼
┌─────────────────────────────┐
│  Generate OAuth URL         │
│  (gmail_auth.py)            │
│  Scopes: gmail.readonly,    │
│          gmail.modify,      │
│          gmail.labels       │
└─────────────────────────────┘
        │
        ▼
User authorizes in browser
        │
        ▼
┌─────────────────────────────┐
│  Exchange code for tokens   │
│  Store in session_state     │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Build Gmail API service    │
│  Fetch user profile         │
└─────────────────────────────┘
```

### 2. Email Fetch Flow

```
User sets filters & clicks "Fetch"
        │
        ▼
┌─────────────────────────────┐
│  build_search_query()       │
│  Constructs Gmail query:    │
│  "older_than:30d is:unread" │
│  + sender/subject filters   │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Gmail API: messages.list() │
│  Returns message IDs        │
│  (max 500 per request)      │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  For each message ID:       │
│  Gmail API: messages.get()  │
│  Fetch metadata (From,      │
│  Subject, Date, Snippet)    │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Calculate sender stats     │
│  Group by sender email      │
│  Sort by count descending   │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  AI categorization          │
│  (if OpenAI configured)     │
│  Classify: newsletter,      │
│  promotional, social, etc.  │
└─────────────────────────────┘
```

### 3. Email Deletion Flow

```
User selects emails & clicks "Delete"
        │
        ▼
┌─────────────────────────────┐
│  batch_trash_emails()       │
│  Uses batchModify API       │
│  Adds TRASH label           │
│  Removes INBOX label        │
└─────────────────────────────┘
        │
        ├── Success ──▶ Update UI, remove from list
        │
        └── Failure ──▶ Fallback to individual
                        trash() calls
```

---

## Key Components

### 1. Gmail Authentication (`auth/gmail_auth.py`)

**Purpose**: Handle Google OAuth 2.0 flow for Gmail access.

**Key Functions**:
| Function | Description |
|----------|-------------|
| `get_gmail_auth_url()` | Generates OAuth consent URL |
| `exchange_code_for_credentials()` | Exchanges auth code for tokens |
| `refresh_credentials()` | Refreshes expired access tokens |
| `get_gmail_service()` | Builds Gmail API client |
| `is_authenticated()` | Checks if user has valid credentials |

**OAuth Scopes Used**:
```python
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",   # Read emails
    "https://www.googleapis.com/auth/gmail.modify",     # Move to trash
    "https://www.googleapis.com/auth/gmail.labels",     # Read labels
]
```

### 2. Gmail Service (`services/gmail_service.py`)

**Purpose**: Interact with Gmail API for email operations.

**Key Functions**:
| Function | Description |
|----------|-------------|
| `build_search_query()` | Constructs Gmail search syntax |
| `fetch_emails()` | Retrieves emails matching query |
| `get_email_details()` | Fetches metadata for single email |
| `batch_trash_emails()` | Bulk moves emails to trash |
| `get_labels()` | Retrieves user's Gmail labels |
| `get_sender_stats()` | Aggregates emails by sender |

**Gmail Query Syntax Examples**:
```
older_than:30d is:unread                    # Basic filter
older_than:30d is:unread from:newsletter    # With sender
older_than:30d is:unread subject:"weekly"   # With subject
```

### 3. AI Service (`services/ai_service.py`)

**Purpose**: Provide intelligent email analysis using OpenAI.

**Key Functions**:
| Function | Description |
|----------|-------------|
| `categorize_senders()` | Groups senders into categories |
| `generate_deletion_summary()` | Creates human-readable summary |
| `get_smart_recommendations()` | Suggests bulk cleanup actions |
| `analyze_email_for_importance()` | Detects email type (newsletter, promo, etc.) |

**Sender Categories**:
- `newsletter` - Regular subscriptions, digests
- `promotional` - Marketing, sales, deals
- `social` - LinkedIn, Twitter, Facebook notifications
- `automated` - System alerts, no-reply addresses
- `potentially_important` - May need review

### 4. UI Components

#### Sidebar (`components/sidebar.py`)
- Filter controls (age, sender, subject, labels)
- Quick filter presets (Newsletters, Promotions, Social, 90+ Days)
- Statistics display (email count, sender count)

#### Email List (`components/email_list.py`)
- Checkbox selection for each email
- Email cards with sender, subject, date, snippet
- Type badges (Newsletter, Promo, Auto, Review)
- Select All / Clear Selection buttons

#### Action Log (`components/action_log.py`)
- Timestamped activity history
- Color-coded by action type
- Session statistics (total deleted)

---

## State Management

All application state is stored in Streamlit's `session_state`:

```python
session_state = {
    # Authentication
    "credentials": OAuth2Credentials,
    "gmail_service": GmailService,
    "user_email": "user@gmail.com",
    "auth_flow": OAuthFlow,
    
    # Email Data
    "emails": [{"id", "from", "subject", "date", ...}],
    "sender_stats": {"sender@email.com": 15, ...},
    "selected_emails": {"msg_id_1", "msg_id_2"},
    "labels": [{"id", "name"}],
    
    # AI Results
    "categories": {"newsletter": [...], "promotional": [...]},
    
    # Logging
    "action_log": [{"timestamp", "type", "description", "status"}],
    "last_query": "older_than:30d is:unread",
}
```

---

## Security Considerations

1. **OAuth Tokens**: Stored only in memory (session_state), not persisted to disk
2. **Credentials File**: `credentials.json` is gitignored
3. **API Keys**: Stored in `.env` file, gitignored
4. **Safe Deletion**: Emails move to Trash (recoverable for 30 days)
5. **Minimal Scopes**: Only requests necessary Gmail permissions

---

## Error Handling

| Scenario | Handling |
|----------|----------|
| OAuth failure | Display error, show setup instructions |
| Gmail API error | Show error message, log to action log |
| Network issues | Graceful degradation, retry suggestion |
| OpenAI unavailable | Fallback to basic summary (no AI) |
| Batch delete fails | Fallback to individual delete calls |

---

## Performance Optimizations

1. **Batch Operations**: Uses `batchModify` for bulk trash operations
2. **Lazy Loading**: Labels fetched only once per session
3. **Pagination**: Limits email display to 50 at a time
4. **Caching**: Sender stats calculated once per fetch

---

## Future Enhancements

- [ ] Scheduled automatic cleanup
- [ ] Multiple Gmail account support
- [ ] Persistent deletion history (database)
- [ ] Email preview before deletion
- [ ] Unsubscribe suggestions
- [ ] Export deleted email list

