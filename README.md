# Gmail Cleanup Agent

A smart email cleanup tool built with Python and Streamlit that helps you delete old unread emails with AI-powered recommendations.

## Features

- **Gmail OAuth Integration**: Securely connect your Gmail account
- **Smart Filtering**: Filter emails by age, sender, subject, and labels
- **AI Recommendations**: Get intelligent suggestions for bulk email cleanup using OpenAI
- **Safe Deletion**: Emails are moved to Trash (recoverable for 30 days)
- **Action Logging**: Track all operations in real-time
- **Sender Analytics**: View email statistics by sender

## Prerequisites

1. **Python 3.10+**
2. **Google Cloud Project** with Gmail API enabled
3. **OpenAI API Key** (optional, for AI recommendations)

## Setup

### 1. Clone and Install Dependencies

```bash
cd jna
pip install -r requirements.txt
```

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as application type
   - Download the JSON file and save it as `credentials.json` in the project root

### 3. Configure Environment

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CREDENTIALS_PATH=credentials.json
```

## Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. **Connect Gmail**: Click "Authorize Gmail Access" and follow the OAuth flow
2. **Set Filters**: Use the sidebar to configure filters (days old, sender, subject, etc.)
3. **Fetch Emails**: Click "Fetch Emails" to retrieve matching emails
4. **Review**: Browse emails and AI recommendations
5. **Select & Delete**: Check emails to delete and click "Delete"

## Project Structure

```
jna/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration and constants
├── auth/
│   └── gmail_auth.py         # Google OAuth2 flow
├── services/
│   ├── gmail_service.py      # Gmail API operations
│   └── ai_service.py         # OpenAI recommendations
├── components/
│   ├── sidebar.py            # Filter controls
│   ├── email_list.py         # Email table with selection
│   └── action_log.py         # Action history display
├── utils/
│   └── logger.py             # In-memory action logging
├── requirements.txt
└── .env.example
```

## Security Notes

- OAuth tokens are stored only in session memory
- Emails are moved to Trash, not permanently deleted
- The app requires minimal Gmail permissions

## License

MIT License
