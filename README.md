# Email Intelligence Assistant

A Streamlit Gmail workspace for inbox prioritization, email summaries, notes, and AI-generated threaded replies.

## Structure

- `backend/`: Gmail authentication, mailbox access, email processing, notes, and AI replies.
- `frontend/`: Streamlit application, reusable UI helpers, and service adapters.
- `credentials.json`: Google OAuth client credentials. Keep private.
- `token.json` and `token_send.json`: generated OAuth tokens. Keep private.
- `email_notes.txt`: generated email notes.

## Run

Activate the existing virtual environment, then run from the project root:

```powershell
.\\mail\\Scripts\\Activate.ps1
streamlit run frontend/app.py
```

The compatibility command also works:

```powershell
streamlit run streamlit_email_frontend.py
```

Set `GEMINI_API_KEY` before using AI replies. OAuth and generated token files should not be committed to source control.
