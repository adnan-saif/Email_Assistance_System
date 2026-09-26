# 📧 AI Email Assistant

> An AI-powered email management and productivity assistant designed to help users read, understand, organize, and respond to emails more efficiently.

## 📌 Overview

**AI Email Assistant** is an intelligent email productivity application that uses artificial intelligence to simplify everyday email tasks.

The assistant can help users understand lengthy emails, generate professional replies, summarize conversations, and improve email-writing efficiency through a simple and intuitive interface.

---

## ✨ Features

- 🤖 **AI-Powered Email Assistant**  
  Interact with an AI assistant to perform common email-related tasks.

- 📝 **Email Draft Generation**  
  Generate professional email drafts based on a short description or instructions.

- 💬 **Smart Reply Suggestions**  
  Create relevant responses to incoming emails.

- 📋 **Email Summarization**  
  Summarize long emails and email conversations into concise points.

- ✨ **Email Improvement**  
  Rewrite emails to make them clearer, more professional, concise, or friendly.

- 🎯 **Tone Adjustment**  
  Adapt emails to different tones such as:
  - Professional
  - Friendly
  - Formal
  - Concise
  - Casual

- 📂 **Email Organization**  
  Assist users in understanding and categorizing emails.

- ⚡ **Productivity Focused**  
  Reduce the time required to read and respond to routine emails.

---

## 🏗️ Project Structure

```text
AI_Email_Assistant/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── ...
│   └── ...
│
├── requirements.txt
├── .gitignore
└── README.md

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
