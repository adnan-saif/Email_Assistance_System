import os
import sys
import html
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend import email_backend as backend

# ---------------------------------------------------------------------------
# Streamlit frontend for the Email Intelligence backend package.
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Email Intelligence Assistant",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Styling -------------------------------------

st.markdown("""
<style>
    .stApp {
        background: #f6f8fb !important;
    }

    /* Force Streamlit's native text variable to black.
       This fixes st.write(), st.caption(), st.markdown() and widget labels. */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        --text-color: #000000 !important;
        --body-text-color: #000000 !important;
        color: #000000 !important;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827 0%, #263449 100%);
        color: #ffffff !important;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(15,23,42,.12);
    }

    .hero h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 750;
        color: #ffffff !important;
    }

    .hero p {
        margin: .35rem 0 0;
        color: #ffffff !important;
    }

    .metric-card {
        padding: 1.05rem 1.15rem;
        border: 1px solid #e5eaf0;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 5px 18px rgba(15,23,42,.05);
        min-height: 120px;
    }

    .metric-title {
        font-size: .86rem;
        color: #64748b !important;
        font-weight: 650;
    }

    .metric-value {
        font-size: 2rem;
        line-height: 1.15;
        font-weight: 760;
        margin-top: .35rem;
        color: #000000 !important;
    }

    .metric-sub {
        color: #64748b !important;
        font-size: .78rem;
        margin-top: .25rem;
    }

    .email-card {
        padding: 1rem 1.1rem;
        border: 1px solid #e5eaf0;
        border-radius: 15px;
        background: #ffffff;
        margin-bottom: .7rem;
        box-shadow: 0 4px 14px rgba(15,23,42,.04);
    }

    .email-subject {
        font-size: 1rem;
        font-weight: 720;
        color: #000000 !important;
    }

    .email-meta {
        color: #000000 !important;
        font-size: .78rem;
        margin-top: .25rem;
    }

    .email-summary {
        color: #000000 !important;
        font-size: .88rem;
        margin-top: .55rem;
    }

    .priority-pill {
        display:inline-block;
        padding:.2rem .55rem;
        border-radius:999px;
        font-size:.72rem;
        font-weight:700;
    }

    .important {
        background:#fee2e2;
        color:#000000 !important;
    }

    .normal {
        background:#fef3c7;
        color:#000000 !important;
    }

    .low {
        background:#f1f5f9;
        color:#000000 !important;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 750;
        color:#0f172a !important;
        margin: .4rem 0 .8rem;
    }

    .reply-box {
        padding: 1rem;
        border: 1px solid #e5eaf0;
        border-radius: 14px;
        background: #ffffff;
        margin-bottom: .8rem;
    }

    /* =========================================================
       FIX: Streamlit's native Markdown/text was inheriting WHITE
       text from the active theme. Make normal app text dark.
       Hero and buttons are explicitly restored below.
       ========================================================= */

    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] em,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6 {
        color: #000000 !important;
    }

    /* The Inbox email rows use st.write/st.caption, which Streamlit
       renders as native elements rather than your custom HTML. */
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stVerticalBlockBorderWrapper"] p,
    [data-testid="stVerticalBlockBorderWrapper"] span {
        color: #000000 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] * {
        color: #000000 !important;
    }


    /* Native Streamlit content inside Inbox / Reply views */
    [data-testid="stMain"] .stMarkdown,
    [data-testid="stMain"] .stMarkdown *,
    [data-testid="stMain"] .stCaption,
    [data-testid="stMain"] .stCaption *,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stMain"] [data-testid="stCaptionContainer"],
    [data-testid="stMain"] [data-testid="stCaptionContainer"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Email rows specifically */
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] * {
        --text-color: #000000 !important;
    }

    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stMarkdown,
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stMarkdown *,
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stCaption,
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stCaption *,
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] p,
    [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Selectbox label and other normal labels */
    label,
    [data-testid="stWidgetLabel"] *,
    [data-testid="stCaptionContainer"] {
        color: #000000 !important;
    }

    /* Selectbox itself */
    [data-baseweb="select"],
    [data-baseweb="select"] > div,
    [data-baseweb="select"] input {
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #dbe2ea !important;
    }

    [data-baseweb="select"] span,
    [role="listbox"] *,
    [role="option"] {
        color: #000000 !important;
    }

    [role="listbox"],
    [role="option"] {
        background: #ffffff !important;
    }

    /* Inputs/text areas */
    textarea,
    input {
        color: #000000 !important;
        background: #ffffff !important;
    }

    /* Buttons stay dark with white text */
    .stButton button,
    .stButton button * {
        color: #ffffff !important;
    }

    /* Priority pills keep their intended colors */
    .priority-pill.important {
        color: #000000 !important;
    }

    .priority-pill.normal {
        color: #000000 !important;
    }

    .priority-pill.low {
        color: #000000 !important;
    }

    /* Hero stays white */
    .hero,
    .hero *,
    .hero h1,
    .hero p {
        color: #ffffff !important;
    }

    .hero p {
        color: #ffffff !important;
    }

    /* Sidebar keeps its dark appearance */
    div[data-testid="stSidebar"] {
        background: #24252d !important;
        border-right: 1px solid #3b3d46;
    }

    div[data-testid="stSidebar"] h1,
    div[data-testid="stSidebar"] h2,
    div[data-testid="stSidebar"] h3,
    div[data-testid="stSidebar"] h4,
    div[data-testid="stSidebar"] p,
    div[data-testid="stSidebar"] span,
    div[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    div[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    div[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * {
        color: #ffffff !important;
    }

    /* Final contrast overrides for Streamlit's higher-specificity elements */
    [data-testid="stMain"] .hero,
    [data-testid="stMain"] .hero *,
    [data-testid="stMain"] .hero h1,
    [data-testid="stMain"] .hero p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stMain"] .stButton button,
    [data-testid="stMain"] .stButton button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        --text-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------- Session state -------------------------------

defaults = {
    "service": None,
    "send_service": None,
    "gemini": None,
    "emails": [],
    "selected_email": None,
    "replies": [],
    "selected_reply": None,
    "sent_result": None,
    "page": "Dashboard",
    "category": "ALL",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------- Helpers -------------------------------------

def priority(email):
    try:
        return backend.analyze_email(email).get("priority", "NORMAL")
    except Exception:
        return "NORMAL"

def grouped(emails):
    result = {"IMPORTANT": [], "NORMAL": [], "LOW": []}
    for e in emails:
        result.setdefault(priority(e), result["NORMAL"]).append(e)
    return result

def connect_gmail():
    with st.spinner("Connecting to Gmail..."):
        st.session_state.service = backend.gmail_login()
    st.success("Gmail connected.")

def load_emails():
    if not st.session_state.service:
        connect_gmail()
    with st.spinner("Loading emails..."):
        st.session_state.emails = backend.get_emails(
            st.session_state.service,
            getattr(backend, "RECENT_EMAIL_COUNT", 50)
        )
    st.session_state.selected_email = None
    st.session_state.replies = []
    st.rerun()

def ensure_gemini():
    if not st.session_state.gemini:
        with st.spinner("Connecting to Gemini..."):
            st.session_state.gemini = backend.get_gemini_client()
    return st.session_state.gemini

def ensure_send_service():
    if not st.session_state.send_service:
        with st.spinner("Authorizing Gmail sending..."):
            st.session_state.send_service = backend.gmail_send_login()
    return st.session_state.send_service

def generate_replies(email):
    gemini = ensure_gemini()
    with st.spinner("Generating 3 professional replies..."):
        context = backend.get_thread_context(
            st.session_state.service, email["id"]
        )
        st.session_state.replies = backend.generate_ai_replies(
            gemini, email, context
        )
    if not st.session_state.replies:
        st.error("Reply generation failed.")
    else:
        st.session_state.selected_reply = 0

def email_label(p):
    return {
        "IMPORTANT": "🔴 Important",
        "NORMAL": "🟡 Normal",
        "LOW": "⚪ Low",
    }.get(p, "🟡 Normal")

# ----------------------------- Sidebar -------------------------------------

with st.sidebar:
    st.markdown("## 📧 Email Intelligence")
    st.caption("Gmail + Gemini powered workspace")
    st.divider()

    nav = st.radio(
        "Workspace",
        ["Dashboard", "Inbox", "Reply Assistant"],
        index=["Dashboard", "Inbox", "Reply Assistant"].index(
            st.session_state.page
        ),
    )
    st.session_state.page = nav

    st.divider()

    if st.button("🔄 Refresh Emails", use_container_width=True):
        load_emails()

    if st.button("🔐 Connect Gmail", use_container_width=True):
        connect_gmail()

    st.divider()
    st.caption("Backend features remain responsible for Gmail access, email parsing, priority analysis, Gemini reply generation, threading and sending.")

# ----------------------------- Header ---------------------------------------

st.markdown("""
<div class="hero">
    <h1>📧 Email Intelligence Assistant</h1>
    <p>Understand your inbox, prioritize messages, and generate professional threaded replies.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Dashboard -----------------------------------

if st.session_state.page == "Dashboard":
    if not st.session_state.emails:
        # Initial screen: load current Gmail data.
        if st.session_state.service is None:
            try:
                connect_gmail()
            except Exception as e:
                st.error(f"Gmail connection failed: {e}")
        if st.session_state.service is not None and not st.session_state.emails:
            try:
                load_emails()
            except Exception as e:
                st.error(f"Could not load emails: {e}")

    groups = grouped(st.session_state.emails)
    total = len(st.session_state.emails)
    important = len(groups["IMPORTANT"])
    normal = len(groups["NORMAL"])
    low = len(groups["LOW"])

    st.markdown('<div class="section-title">Inbox Overview</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "📨 Total Emails", total, "Currently loaded"),
        (c2, "🔴 Important", important, "Requires attention"),
        (c3, "🟡 Normal", normal, "Regular messages"),
        (c4, "⚪ Low", low, "Low-priority messages"),
    ]
    for col, title, value, sub in cards:
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-title">{title}</div>'
                f'<div class="metric-value">{value}</div>'
                f'<div class="metric-sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.write("")
    st.markdown('<div class="section-title">Priority Sections</div>', unsafe_allow_html=True)

    tabs = st.tabs(["🔴 Important", "🟡 Normal", "⚪ Low"])
    for tab, key in zip(tabs, ["IMPORTANT", "NORMAL", "LOW"]):
        with tab:
            items = groups[key]
            if not items:
                st.info("No emails in this category.")
            else:
                for e in items[:10]:
                    p = priority(e).lower()
                    summary = backend.create_clean_summary(e.get("body", ""))
                    st.markdown(
                        f'<div class="email-card">'
                        f'<span class="priority-pill {p}">{email_label(key)}</span>'
                        f'<div class="email-subject">{html.escape(e.get("subject","(No Subject)"))}</div>'
                        f'<div class="email-meta">{html.escape(e.get("sender",""))} · {e.get("date","")} · {e.get("time","")}</div>'
                        f'<div class="email-summary">{html.escape(summary[:280])}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

    st.write("")
    if st.button("✉️ Open Reply Assistant", type="primary"):
        st.session_state.page = "Reply Assistant"
        st.rerun()

# ----------------------------- Inbox ---------------------------------------

elif st.session_state.page == "Inbox":
    st.markdown('<div class="section-title">Inbox</div>', unsafe_allow_html=True)

    if not st.session_state.emails:
        st.info("No emails loaded yet.")
        if st.button("Load Gmail Emails", type="primary"):
            load_emails()
        st.stop()

    groups = grouped(st.session_state.emails)
    choice = st.selectbox(
        "Email category",
        ["ALL", "IMPORTANT", "NORMAL", "LOW"],
        format_func=lambda x: {
            "ALL": "📨 All Emails",
            "IMPORTANT": "🔴 Important Emails",
            "NORMAL": "🟡 Normal Emails",
            "LOW": "⚪ Low Emails",
        }[x],
    )

    shown = st.session_state.emails if choice == "ALL" else groups[choice]
    st.caption(f"{len(shown)} email(s)")

    for i, e in enumerate(shown):
        p = priority(e)
        summary = backend.create_clean_summary(e.get("body", ""))
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"### {email_label(p)}  {e.get('subject','(No Subject)')}")
                st.caption(f"{e.get('sender','')} · {e.get('date','')} · {e.get('time','')}")
                st.write(summary)
            with right:
                if st.button("Reply", key=f"inbox_reply_{choice}_{i}"):
                    st.session_state.selected_email = e
                    st.session_state.page = "Reply Assistant"
                    st.session_state.replies = []
                    st.rerun()

# ----------------------------- Reply Assistant -----------------------------

else:
    st.markdown('<div class="section-title">Reply Assistant</div>', unsafe_allow_html=True)

    if not st.session_state.emails:
        st.info("Load your Gmail emails first.")
        if st.button("Load Emails", type="primary"):
            load_emails()
        st.stop()

    groups = grouped(st.session_state.emails)

    # Category cards / selector: all available emails, not only 20.
    st.markdown("### 1. Choose an email category")
    a, b, c, d = st.columns(4)
    category_buttons = [
        (a, "ALL", "📨 All", len(st.session_state.emails)),
        (b, "IMPORTANT", "🔴 Important", len(groups["IMPORTANT"])),
        (c, "NORMAL", "🟡 Normal", len(groups["NORMAL"])),
        (d, "LOW", "⚪ Low", len(groups["LOW"])),
    ]
    for col, key, label, count in category_buttons:
        with col:
            if st.button(f"{label}\n{count}", key=f"cat_{key}", use_container_width=True):
                st.session_state.category = key
                st.session_state.selected_email = None
                st.session_state.replies = []
                st.rerun()

    category = st.session_state.category
    available = (
        st.session_state.emails
        if category == "ALL"
        else groups[category]
    )

    st.markdown(f"### 2. Select an email · {len(available)} available")

    if not available:
        st.warning("No emails are available in this category.")
        st.stop()

    options = list(range(len(available)))
    labels = []
    for i in options:
        e = available[i]
        labels.append(
            f"{i+1}. {e.get('subject','(No Subject)')} — "
            f"{e.get('sender','(Unknown)')}"
        )

    selected_index = st.selectbox(
        "Email",
        options,
        format_func=lambda i: labels[i],
    )
    selected = available[selected_index]

    with st.container(border=True):
        p = priority(selected)
        st.markdown(f"### {email_label(p)}  {selected.get('subject','(No Subject)')}")
        st.caption(
            f"From: {selected.get('sender','')} · "
            f"{selected.get('date','')} · {selected.get('time','')}"
        )
        st.write(backend.create_clean_summary(selected.get("body", "")))

        with st.expander("View full email"):
            st.write(selected.get("body", ""))

        if selected.get("links"):
            with st.expander("🔗 Links"):
                for link in selected["links"]:
                    st.markdown(f"- {link}")

        if selected.get("attachments"):
            with st.expander("📎 Attachments"):
                for attachment in selected["attachments"]:
                    st.write(
                        f"{attachment.get('filename','Unknown')} "
                        f"({attachment.get('mime_type','')})"
                    )

    if st.button("✨ Generate 3 AI Replies", type="primary", use_container_width=True):
        st.session_state.selected_email = selected
        generate_replies(selected)

    if st.session_state.replies:
        st.markdown("### 3. Choose a reply")

        names = [
            "Professional",
            "Warm & Professional",
            "Concise",
        ]

        reply_tabs = st.tabs(names)
        for idx, (tab, reply) in enumerate(zip(reply_tabs, st.session_state.replies)):
            with tab:
                st.text_area(
                    "Generated reply",
                    reply,
                    height=300,
                    key=f"reply_text_{idx}",
                )
                if st.button(
                    f"Use {names[idx]} Reply",
                    key=f"use_reply_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.selected_reply = idx
                    st.rerun()

        if st.session_state.selected_reply is not None:
            idx = st.session_state.selected_reply
            st.markdown("### 4. Edit before sending")

            edited = st.text_area(
                "Final reply",
                st.session_state.replies[idx],
                height=300,
                key="final_reply_editor",
            )

            st.markdown("### 5. Send")
            st.warning(
                f"You are about to send this reply to "
                f"{selected.get('sender','the recipient')}."
            )

            if st.button("📤 Send Reply Through Gmail", type="primary", use_container_width=True):
                try:
                    send_service = ensure_send_service()
                    with st.spinner("Sending threaded reply..."):
                        result = backend.send_gmail_reply(
                            st.session_state.service,
                            send_service,
                            selected["id"],
                            edited.strip(),
                        )
                    st.session_state.sent_result = result
                    if result.get("success"):
                        st.success("✅ Reply sent successfully.")
                    else:
                        st.error(f"Failed to send reply: {result.get('error','Unknown error')}")
                except Exception as e:
                    st.error(f"Could not send reply: {e}")

            if st.session_state.sent_result and st.session_state.sent_result.get("success"):
                st.info(
                    f"Recipient: {st.session_state.sent_result.get('recipient','')} · "
                    f"Message ID: {st.session_state.sent_result.get('message_id','')}"
                )

# Footer
st.divider()
st.caption("Email Intelligence Assistant · Streamlit frontend · Existing backend functions are reused.")
