import os
import re
import time
import base64
import html
from datetime import datetime
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "credentials.json")
READ_TOKEN_FILE = os.path.join(PROJECT_ROOT, "token.json")


def load_env_file(path):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(os.path.join(PROJECT_ROOT, ".env"))


# ============================================================
# CONFIGURATION
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

NOTES_FILE = os.path.join(PROJECT_ROOT, "email_notes.txt")

# How often to check Gmail
CHECK_INTERVAL = 30

# Number of recent emails to check
RECENT_EMAIL_COUNT = 50


# ============================================================
# GMAIL LOGIN
# ============================================================

def gmail_login():

    creds = None

    if os.path.exists(READ_TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            READ_TOKEN_FILE,
            SCOPES
        )

    if not creds or not creds.valid:

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        creds = flow.run_local_server(
            port=0
        )

        with open(
            READ_TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                creds.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ============================================================
# DECODE EMAIL BODY
# ============================================================

def decode_body(data):

    if not data:
        return ""

    try:

        return base64.urlsafe_b64decode(
            data
        ).decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove zero-width and invisible Unicode characters
    text = re.sub(
        r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F"
        r"\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF]",
        "",
        text
    )

    # Normalize non-breaking spaces
    text = text.replace(
        "\xa0",
        " "
    )

    # Remove excessive whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# REMOVE HTML
# ============================================================

def clean_html(text):

    if not text:
        return ""

    # Remove scripts completely
    text = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Remove styles completely
    text = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Remove noscript blocks
    text = re.sub(
        r"<noscript\b[^>]*>.*?</noscript>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    # Convert common block-level HTML elements to spaces
    text = re.sub(
        r"</?(?:br|p|div|li|tr|td|th|h[1-6])\b[^>]*>",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Remove all remaining HTML tags
    text = re.sub(
        r"<[^>]*>",
        " ",
        text
    )

    # Decode entities and clean whitespace
    text = html.unescape(
        text
    )

    return clean_text(
        text
    )


# ============================================================
# EXTRACT RELEVANT LINKS
# ============================================================

def extract_links(text):
    """
    Extract only useful document/resource links from the email.

    Rules:
    - Keep a maximum of 3 links per email.
    - Keep only HTTP/HTTPS links.
    - Prefer actual document/sheet/file/resource links.
    - Ignore obvious tracking, unsubscribe, social, image,
      pixel, and marketing links.
    - Never invent a link.
    """

    if not text:
        return []

    links = []

    # --------------------------------------------------------
    # HTML href links
    # --------------------------------------------------------

    href_pattern = r"""href\s*=\s*["']([^"']+)["']"""

    href_links = re.findall(
        href_pattern,
        text,
        flags=re.IGNORECASE
    )

    links.extend(href_links)

    # --------------------------------------------------------
    # Visible URLs
    # --------------------------------------------------------

    url_pattern = r"""https?://[^\s<>"']+"""

    visible_links = re.findall(
        url_pattern,
        text,
        flags=re.IGNORECASE
    )

    links.extend(visible_links)

    # --------------------------------------------------------
    # Clean, filter and deduplicate
    # --------------------------------------------------------

    cleaned_links = []

    ignored_patterns = [
        # Tracking / analytics
        r"google-analytics",
        r"googletagmanager",
        r"doubleclick",
        r"pixel",
        r"tracking",
        r"track\?",
        r"click\?",
        r"open\?",
        r"beacon",

        # Unsubscribe / email preferences
        r"unsubscribe",
        r"preferences",
        r"email-preferences",
        r"manage-preferences",

        # Common marketing/social links
        r"facebook\.com",
        r"instagram\.com",
        r"twitter\.com",
        r"x\.com",
        r"linkedin\.com",
        r"youtube\.com",

        # Image / asset links
        r"\.(?:png|jpg|jpeg|gif|svg|webp)(?:\?|$)",

        # Tracking query parameters
        r"[?&]utm_",
        r"[?&]fbclid=",
        r"[?&]gclid=",
        r"[?&]mc_cid=",
        r"[?&]mc_eid=",
    ]

    # Strong indicators of useful email resources
    useful_patterns = [
        # Google
        r"docs\.google\.com",
        r"sheets\.google\.com",
        r"drive\.google\.com",
        r"slides\.google\.com",
        r"forms\.google\.com",

        # Microsoft
        r"sharepoint\.com",
        r"onedrive\.live\.com",
        r"1drv\.ms",
        r"office\.com",

        # Common document/file services
        r"dropbox\.com",
        r"box\.com",
        r"notion\.so",
        r"canva\.com",
        r"figma\.com",
        r"github\.com",

        # Generic file/resource indicators
        r"\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|csv|txt|zip)(?:\?|$)",
        r"/(?:document|documents|doc|sheet|sheets|spreadsheet|"
        r"file|files|download|attachment|attachments|resource|"
        r"resources|report|reports)(?:/|\?|$)",
    ]

    for link in links:

        if not link:
            continue

        link = html.unescape(
            link
        ).strip()

        link = link.strip(
            " <>\"'()[]{}"
        )

        link = link.rstrip(
            ".,;:!?"
        )

        if not link.lower().startswith(
            ("http://", "https://")
        ):
            continue

        lower_link = link.lower()

        # Ignore obvious junk/tracking links
        if any(
            re.search(pattern, lower_link)
            for pattern in ignored_patterns
        ):
            continue

        # Only keep links that look like actual resources.
        # This prevents arbitrary marketing/navigation URLs
        # from being shown as email links.
        if not any(
            re.search(pattern, lower_link)
            for pattern in useful_patterns
        ):
            continue

        if link not in cleaned_links:
            cleaned_links.append(link)

        # Maximum 3 links
        if len(cleaned_links) >= 3:
            break

    return cleaned_links


# ============================================================
# REMOVE LINKS FROM TEXT
# ============================================================

def remove_links(text):

    if not text:
        return ""

    # Remove HTTP / HTTPS URLs
    text = re.sub(
        r"https?://[^\s<>'\"]+",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Remove www URLs
    text = re.sub(
        r"\bwww\.[^\s<>'\"]+",
        " ",
        text,
        flags=re.IGNORECASE
    )

    return text


# ============================================================
# EXTRACT EMAIL ATTACHMENTS
# ============================================================

def extract_attachments(payload):
    """
    Recursively extract actual file attachments from the Gmail payload.

    Returns a list containing the attachment filename and MIME type.
    Attachments are only listed when Gmail provides a real filename /
    attachmentId. No fake attachment names are generated.
    """

    attachments = []

    def walk_parts(part):
        filename = part.get("filename", "").strip()
        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        # A real Gmail attachment normally has a filename and attachmentId.
        if filename and attachment_id:
            attachment = {
                "filename": filename,
                "mime_type": part.get("mimeType", "application/octet-stream")
            }

            if attachment not in attachments:
                attachments.append(attachment)

        for child in part.get("parts", []):
            walk_parts(child)

    walk_parts(payload)

    return attachments


# ============================================================
# GET EMAIL BODY
# ============================================================

def get_email_body(payload):

    plain_parts = []
    html_parts = []

    # --------------------------------------------------------
    # Direct body
    # --------------------------------------------------------

    body_data = (
        payload
        .get("body", {})
        .get("data")
    )

    if body_data:

        body = decode_body(
            body_data
        )

        mime_type = payload.get(
            "mimeType",
            ""
        ).lower()

        if mime_type == "text/html":

            html_parts.append(
                body
            )

        else:

            plain_parts.append(
                body
            )

    # --------------------------------------------------------
    # Multipart email
    # --------------------------------------------------------

    parts = payload.get(
        "parts",
        []
    )

    for part in parts:

        mime_type = part.get(
            "mimeType",
            ""
        ).lower()

        part_data = (
            part
            .get("body", {})
            .get("data")
        )

        if mime_type == "text/plain":

            if part_data:

                plain_parts.append(
                    decode_body(
                        part_data
                    )
                )

        elif mime_type == "text/html":

            if part_data:

                html_parts.append(
                    decode_body(
                        part_data
                    )
                )

        elif part.get("parts"):

            nested_body = get_email_body(
                part
            )

            if nested_body:

                plain_parts.append(
                    nested_body
                )

    # --------------------------------------------------------
    # Prefer plain text
    # --------------------------------------------------------

    plain_text = "\n".join(
        plain_parts
    ).strip()

    if plain_text:

        return clean_text(
            plain_text
        )

    # --------------------------------------------------------
    # Otherwise use cleaned HTML
    # --------------------------------------------------------

    html_text = "\n".join(
        html_parts
    ).strip()

    if html_text:

        return clean_html(
            html_text
        )

    return ""


# ============================================================
# GET RAW MIME CONTENT
# ============================================================

def get_raw_mime_content(payload):

    """
    Recursively collect the original decoded MIME content.

    This is used for link extraction because HTML href
    attributes must be inspected before HTML is cleaned.
    """

    contents = []

    body_data = (
        payload
        .get("body", {})
        .get("data")
    )

    if body_data:

        decoded = decode_body(
            body_data
        )

        if decoded:

            contents.append(
                decoded
            )

    for part in payload.get(
        "parts",
        []
    ):

        contents.extend(
            get_raw_mime_content(
                part
            )
        )

    return contents


# ============================================================
# FORMAT DATE / TIME
# ============================================================

def format_email_datetime(date_string):

    try:

        dt = parsedate_to_datetime(
            date_string
        )

        date_value = dt.strftime(
            "%d %b %Y"
        )

        time_value = dt.strftime(
            "%I:%M %p"
        )

        return (
            date_value,
            time_value
        )

    except Exception:

        return (
            "Unknown date",
            "Unknown time"
        )


# ============================================================
# GET RECENT EMAILS
# ============================================================

def get_emails(
    service,
    max_results=50
):

    try:

        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                maxResults=max_results,
                q="in:anywhere"
            )
            .execute()
        )

    except Exception as error:

        print(
            f"❌ Gmail error: {error}"
        )

        return []

    messages = results.get(
        "messages",
        []
    )

    emails = []

    for message in messages:

        try:

            email = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=message["id"],
                    format="full"
                )
                .execute()
            )

            payload = email.get(
                "payload",
                {}
            )

            # ------------------------------------------------
            # Extract actual email attachments
            # ------------------------------------------------

            attachments = extract_attachments(
                payload
            )

            headers = payload.get(
                "headers",
                []
            )

            subject = "(No Subject)"
            sender = "(Unknown Sender)"
            date_string = ""

            # ------------------------------------------------
            # Read headers
            # ------------------------------------------------

            for header in headers:

                name = header.get(
                    "name",
                    ""
                ).lower()

                value = header.get(
                    "value",
                    ""
                )

                if name == "subject":

                    subject = value.strip()

                elif name == "from":

                    sender = value.strip()

                elif name == "date":

                    date_string = value.strip()

            # ------------------------------------------------
            # Format date
            # ------------------------------------------------

            date, time_value = (
                format_email_datetime(
                    date_string
                )
            )

            # ------------------------------------------------
            # Get body
            # ------------------------------------------------

            body = get_email_body(
                payload
            )

            # ------------------------------------------------
            # Extract links BEFORE cleaning/truncating
            # ------------------------------------------------

            links = []

            # Extract from all decoded MIME parts
            raw_parts = get_raw_mime_content(
                payload
            )

            for raw_part in raw_parts:

                for link in extract_links(
                    raw_part
                ):

                    if link not in links:

                        links.append(
                            link
                        )

            # Extract visible URLs from body too
            for link in extract_links(
                body
            ):

                if link not in links:

                    links.append(
                        link
                    )

            # ------------------------------------------------
            # Limit body only after links are extracted
            # ------------------------------------------------

            body = body[:10000]

            emails.append({

                "id": message["id"],

                "sender": sender,

                "subject": subject,

                "body": body,

                "links": links,

                "attachments": attachments,

                "date": date,

                "time": time_value,

                "timestamp": date_string
            })

        except Exception as error:

            print(
                f"⚠️ Could not process email: {error}"
            )

    return emails


# ============================================================
# CREATE CLEAN SUMMARY
# ============================================================

def create_clean_summary(body):

    if not body:

        return "No readable email content."

    # --------------------------------------------------------
    # Remove URLs FIRST
    # --------------------------------------------------------

    summary = remove_links(
        body
    )

    # --------------------------------------------------------
    # Remove any remaining HTML
    # --------------------------------------------------------

    summary = clean_html(
        summary
    )

    # --------------------------------------------------------
    # Remove email-style tracking fragments
    # --------------------------------------------------------

    summary = re.sub(
        r"\b(?:utm_source|utm_medium|utm_campaign|"
        r"utm_term|utm_content)=[^\s]+",
        " ",
        summary,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Remove invisible characters
    # --------------------------------------------------------

    summary = re.sub(
        r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F"
        r"\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF]",
        "",
        summary
    )

    # --------------------------------------------------------
    # Decode entities again in case they survived
    # --------------------------------------------------------

    summary = html.unescape(
        summary
    )

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    summary = re.sub(
        r"\s+",
        " ",
        summary
    ).strip()

    # --------------------------------------------------------
    # Remove leading/trailing punctuation
    # --------------------------------------------------------

    summary = summary.strip(
        " \t\r\n|:-"
    )

    if not summary:

        return "No readable email content."

    # --------------------------------------------------------
    # Limit summary length
    # --------------------------------------------------------

    max_length = 300

    if len(summary) > max_length:

        summary = (
            summary[:max_length]
            .rsplit(" ", 1)[0]
            .rstrip()
            + "..."
        )

    return summary


# ============================================================
# ANALYZE EMAIL
# ============================================================

def analyze_email(email):

    subject = email.get(
        "subject",
        ""
    )

    body = email.get(
        "body",
        ""
    )

    # --------------------------------------------------------
    # Priority analysis
    # --------------------------------------------------------

    text = (
        subject
        + " "
        + body
    ).lower()

    important_words = [
        "urgent",
        "important",
        "deadline",
        "due",
        "submit",
        "submission",
        "meeting",
        "action required",
        "asap",
        "required",
        "please complete",
        "please send",
        "respond",
        "response required",
        "last date",
        "final date",
        "interview",
        "appointment",
        "payment due",
        "approval required"
    ]

    low_priority_words = [
        "unsubscribe",
        "newsletter",
        "promotion",
        "sale",
        "discount",
        "advertisement",
        "marketing"
    ]

    # --------------------------------------------------------
    # Determine priority
    # --------------------------------------------------------

    if any(
        word in text
        for word in important_words
    ):

        priority = "IMPORTANT"

    elif any(
        word in text
        for word in low_priority_words
    ):

        priority = "LOW"

    else:

        priority = "NORMAL"

    # --------------------------------------------------------
    # Determine action
    # --------------------------------------------------------

    if priority == "IMPORTANT":

        action_required = True

        action = (
            "Review and take required action"
        )

    else:

        action_required = False

        action = "None"

    # --------------------------------------------------------
    # CLEAN SUMMARY
    # --------------------------------------------------------

    summary = create_clean_summary(
        body
    )

    return {

        "summary": summary,

        "priority": priority,

        "action_required": action_required,

        "action": action,

        "deadline": None,

        "links": email.get(
            "links",
            []
        )[:3],

        "attachments": email.get(
            "attachments",
            []
        )
    }


# ============================================================
# READ EXISTING EMAIL IDS
# ============================================================

def get_saved_email_ids():

    if not os.path.exists(
        NOTES_FILE
    ):

        return set()

    try:

        with open(
            NOTES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

        ids = set(
            re.findall(
                r"EMAIL_ID:([^\s]+)",
                content
            )
        )

        return ids

    except Exception:

        return set()


# ============================================================
# CREATE NOTE
# ============================================================

def create_note(
    email,
    analysis
):

    priority = analysis.get(
        "priority",
        "NORMAL"
    )

    # --------------------------------------------------------
    # Priority icon
    # --------------------------------------------------------

    if priority == "IMPORTANT":

        icon = "🔴"

    elif priority == "LOW":

        icon = "⚪"

    else:

        icon = "🟡"

    # --------------------------------------------------------
    # Start note
    # --------------------------------------------------------

    note = (
        "============================================================\n"
        f"EMAIL_ID:{email['id']}\n"
        "============================================================\n\n"

        f"{icon} {email['subject']}\n\n"

        f"📅 Date      : {email['date']}\n"
        f"🕐 Time      : {email['time']}\n"
        f"👤 From      : {email['sender']}\n"
        f"🏷️ Priority  : {priority}\n\n"

        f"📝 Summary   : {analysis.get('summary', 'No summary')}\n\n"
    )

    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------

    note += (
        "✅ Action    : "
        f"{analysis.get('action', 'None')}\n"
    )

    # --------------------------------------------------------
    # Deadline
    # --------------------------------------------------------

    if analysis.get(
        "deadline"
    ):

        note += (
            "⏰ Deadline  : "
            f"{analysis['deadline']}\n"
        )

    # --------------------------------------------------------
    # LINKS
    # Always show the section.
    # If no relevant links were found, show "None".
    # --------------------------------------------------------

    links = analysis.get(
        "links",
        []
    )

    note += "\n"
    note += "🔗 Links:\n"

    if links:
        for index, link in enumerate(
            links[:3],
            start=1
        ):
            note += (
                f"{index}. {link}\n"
            )
    else:
        note += "None\n"

    # --------------------------------------------------------
    # ATTACHMENTS
    # Always show the section.
    # If no actual attachments were found, show "None".
    # --------------------------------------------------------

    attachments = analysis.get(
        "attachments",
        []
    )

    note += "\n"
    note += "📎 Attachments:\n"

    if attachments:
        for index, attachment in enumerate(
            attachments,
            start=1
        ):
            filename = attachment.get(
                "filename",
                "Unknown file"
            )
            mime_type = attachment.get(
                "mime_type",
                ""
            )

            if mime_type:
                note += (
                    f"{index}. {filename} "
                    f"({mime_type})\n"
                )
            else:
                note += (
                    f"{index}. {filename}\n"
                )
    else:
        note += "None\n"

    # --------------------------------------------------------
    # End note
    # --------------------------------------------------------

    note += (
        "\n"
        "============================================================\n"
    )

    return note


# ============================================================
# UPDATE EMAIL PRIORITY COUNTS
# ============================================================

def update_email_priority_counts():
    """Update IMPORTANT, NORMAL and LOW email counts at the top."""

    if not os.path.exists(NOTES_FILE):
        return

    try:
        with open(
            NOTES_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            content = file.read()

        important_count = len(re.findall(
            r"(?m)^🏷️ Priority  : IMPORTANT\s*$",
            content
        ))

        normal_count = len(re.findall(
            r"(?m)^🏷️ Priority  : NORMAL\s*$",
            content
        ))

        low_count = len(re.findall(
            r"(?m)^🏷️ Priority  : LOW\s*$",
            content
        ))

        count_block = (
            "📊 EMAIL COUNTS\n"
            f"🔴 Important : {important_count}\n"
            f"🟡 Normal    : {normal_count}\n"
            f"⚪ Low       : {low_count}\n\n"
        )

        # Remove the previous count block, if present.
        content = re.sub(
            r"📊 EMAIL COUNTS\n"
            r"🔴 Important : \d+\n"
            r"🟡 Normal    : \d+\n"
            r"⚪ Low       : \d+\n\n",
            "",
            content,
            count=1
        )

        # Insert the fresh count block immediately after the header.
        header_end = (
            "📧 EMAIL INTELLIGENCE NOTES\n"
            "============================================================\n\n"
        )

        if header_end in content:
            content = content.replace(
                header_end,
                header_end + count_block,
                1
            )
        else:
            content = count_block + content

        with open(
            NOTES_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

    except Exception as error:
        print(
            f"⚠️ Could not update email counts: {error}"
        )


# ============================================================
# CREATE / INITIALIZE NOTES FILE
# ============================================================

def initialize_notes_file():

    if os.path.exists(
        NOTES_FILE
    ):

        return

    with open(
        NOTES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "============================================================\n"
        )

        file.write(
            "📧 EMAIL INTELLIGENCE NOTES\n"
        )

        file.write(
            "============================================================\n\n"
        )

        file.write(
            "Created: "
            + datetime.now().strftime(
                "%d %b %Y, %I:%M %p"
            )
            + "\n\n"
        )

        file.write(
            "📊 EMAIL COUNTS\n"
            "🔴 Important : 0\n"
            "🟡 Normal    : 0\n"
            "⚪ Low       : 0\n\n"
        )


# ============================================================
# ADD NEW NOTE TO TOP
# ============================================================

def add_note_to_top(note):

    initialize_notes_file()

    try:

        with open(
            NOTES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            existing = file.read()

        marker = (
            "============================================================"
        )

        # Find the separator that starts the first email
        first_email = existing.find(
            marker,
            existing.find(marker) + len(marker)
        )

        if first_email == -1:

            updated = (
                existing
                + "\n"
                + note
            )

        else:

            header = existing[
                :first_email
            ]

            emails = existing[
                first_email:
            ]

            updated = (
                header
                + note
                + "\n"
                + emails
            )

        with open(
            NOTES_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                updated
            )

        update_email_priority_counts()

    except Exception as error:

        print(
            f"❌ Could not update notes: {error}"
        )


# ============================================================
# PROCESS EMAIL
# ============================================================

def process_new_email(email):

    analysis = analyze_email(
        email
    )

    note = create_note(
        email,
        analysis
    )

    add_note_to_top(
        note
    )

    print("\n")
    print("=" * 60)

    print(
        "📩 EMAIL PROCESSED"
    )

    print(
        f"Subject : {email['subject']}"
    )

    print(
        f"From    : {email['sender']}"
    )

    print(
        f"Date    : {email['date']}"
    )

    print(
        f"Time    : {email['time']}"
    )

    print(
        f"Priority: {analysis['priority']}"
    )

    print(
        f"Summary : {analysis['summary'][:150]}"
    )

    print(
        f"Links   : {len(analysis.get('links', []))}"
    )

    print(
        f"Attachments: {len(analysis.get('attachments', []))}"
    )

    print(
        "✅ Added to email_notes.txt"
    )

    print("=" * 60)


# ============================================================
# INITIALIZE FIRST 50 EMAILS
# ============================================================

def initialize_recent_emails(service):

    print("\n")
    print("=" * 60)

    print(
        "📥 FIRST RUN"
    )

    print(
        f"Reading the {RECENT_EMAIL_COUNT} most recent emails..."
    )

    print("=" * 60)

    emails = get_emails(
        service,
        RECENT_EMAIL_COUNT
    )

    if not emails:

        print(
            "❌ No emails found."
        )

        return

    saved_ids = get_saved_email_ids()

    new_count = 0

    # Gmail normally returns newest first.
    # Process oldest -> newest.
    emails.reverse()

    for email in emails:

        if email["id"] in saved_ids:

            continue

        process_new_email(
            email
        )

        new_count += 1

    print("\n")

    print(
        "✅ Initial setup complete."
    )

    update_email_priority_counts()

    print(
        f"📨 New emails processed: {new_count}"
    )


# ============================================================
# CONTINUOUS MONITOR
# ============================================================

def monitor_emails(service):

    print("\n")
    print("=" * 60)

    print(
        "👀 CONTINUOUS EMAIL MONITOR STARTED"
    )

    print(
        f"🔄 Checking Gmail every {CHECK_INTERVAL} seconds"
    )

    print(
        "📄 Notes: email_notes.txt"
    )

    print(
        "Press CTRL+C to stop."
    )

    print("=" * 60)

    while True:

        try:

            emails = get_emails(
                service,
                RECENT_EMAIL_COUNT
            )

            saved_ids = get_saved_email_ids()

            new_emails = []

            for email in emails:

                if email["id"] not in saved_ids:

                    new_emails.append(
                        email
                    )

            # Process oldest first
            new_emails.reverse()

            for email in new_emails:

                process_new_email(
                    email
                )

            if not new_emails:

                print(
                    f"⏳ "
                    f"{datetime.now().strftime('%I:%M:%S %p')} "
                    f"— No new emails."
                )

            time.sleep(
                CHECK_INTERVAL
            )

        except KeyboardInterrupt:

            print(
                "\n\n🛑 Email monitor stopped."
            )

            break

        except Exception as error:

            print(
                f"\n⚠️ Monitor error: {error}"
            )

            print(
                "Retrying..."
            )

            time.sleep(
                CHECK_INTERVAL
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 60)

    print(
        "📧 EMAIL INTELLIGENCE ASSISTANT"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Gmail login
    # --------------------------------------------------------

    service = gmail_login()

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Rebuild the TXT file every time the program is started.
    #
    # This ensures old emails are regenerated using:
    #   - clean Summary
    #   - separate Links section
    #   - new structure
    #
    # Once everything is confirmed working, this can be removed
    # if you want to preserve the existing notes.
    # --------------------------------------------------------

    if os.path.exists(
        NOTES_FILE
    ):

        print(
            "\n🧹 Rebuilding email_notes.txt "
            "using the new structure..."
        )

        os.remove(
            NOTES_FILE
        )

    initialize_notes_file()

    # --------------------------------------------------------
    # Process recent emails
    # --------------------------------------------------------

    initialize_recent_emails(
        service
    )

    # --------------------------------------------------------
    # Start monitor
    # --------------------------------------------------------

    monitor_emails(
        service
    )



# ============================================================
# AI EMAIL REPLY ASSISTANT - ADDED FEATURE
# ============================================================
#
# The original application above is kept intact.
# This section adds:
#   - Gemini-powered reply generation
#   - 3 professional reply versions
#   - Terminal selection/editing
#   - Gmail threaded reply sending
#
# Required:
#   pip install google-genai
#
# Environment variable:
#   GEMINI_API_KEY=your_api_key
#
# The current Google Gemini API examples use Gemini 3.x Flash.
# Change GEMINI_MODEL below if your account provides a different
# Flash model.
# ============================================================

import json
from email.message import EmailMessage
from email.utils import parseaddr

# Gemini configuration
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash"
)

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# Separate Gmail token for sending.
# This keeps the original read-only Gmail login/token untouched.
GMAIL_SEND_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

GMAIL_SEND_TOKEN_FILE = os.path.join(PROJECT_ROOT, "token_send.json")


# ============================================================
# GEMINI LOGIN
# ============================================================

def get_gemini_client():
    """
    Create the Gemini client using GEMINI_API_KEY.

    The key is read from the environment. If it is not present,
    the user can enter it in the terminal for the current run.
    """

    api_key = os.getenv(GEMINI_API_KEY_ENV, "").strip()

    if not api_key:
        print("\n🔑 GEMINI_API_KEY was not found in environment.")
        api_key = input(
            "Enter your Gemini API key for this session: "
        ).strip()

    if not api_key:
        raise ValueError(
            "Gemini API key is required to generate AI replies."
        )

    try:
        from google import genai
    except ImportError:
        raise ImportError(
            "The Gemini SDK is not installed.\n"
            "Run: pip install google-genai"
        )

    return genai.Client(api_key=api_key)


# ============================================================
# GMAIL SEND LOGIN
# ============================================================

def gmail_send_login():
    """
    Separate Gmail authorization used only for sending replies.

    The original gmail_login() function remains unchanged and
    continues to use the existing read-only token.
    """

    creds = None

    if os.path.exists(GMAIL_SEND_TOKEN_FILE):

        creds = Credentials.from_authorized_user_file(
            GMAIL_SEND_TOKEN_FILE,
            GMAIL_SEND_SCOPES
        )

    if not creds or not creds.valid:

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            GMAIL_SEND_SCOPES
        )

        creds = flow.run_local_server(
            port=0
        )

        with open(
            GMAIL_SEND_TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                creds.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


# ============================================================
# GET FULL EMAIL / THREAD INFORMATION
# ============================================================

def get_full_email_for_reply(service, email_id):
    """
    Get the selected email again so we can obtain Gmail's
    threadId and Message-ID headers for a proper threaded reply.
    """

    return (
        service.users()
        .messages()
        .get(
            userId="me",
            id=email_id,
            format="full"
        )
        .execute()
    )


def get_header_value(payload, header_name):
    """
    Read one header from a Gmail payload.
    """

    for header in payload.get("headers", []):

        if (
            header.get("name", "").lower()
            == header_name.lower()
        ):

            return header.get(
                "value",
                ""
            ).strip()

    return ""


def get_thread_context(service, email_id):
    """
    Collect recent messages from the selected Gmail thread.

    This gives Gemini conversation context instead of generating
    a reply from only the latest message.
    """

    try:

        selected = get_full_email_for_reply(
            service,
            email_id
        )

        thread_id = selected.get(
            "threadId"
        )

        if not thread_id:
            return ""

        thread_result = (
            service.users()
            .threads()
            .get(
                userId="me",
                id=thread_id,
                format="full"
            )
            .execute()
        )

        messages = thread_result.get(
            "messages",
            []
        )

        context_parts = []

        # Keep the latest messages so the prompt does not grow
        # unnecessarily large.
        messages = messages[-8:]

        for message in messages:

            payload = message.get(
                "payload",
                {}
            )

            sender = get_header_value(
                payload,
                "From"
            )

            subject = get_header_value(
                payload,
                "Subject"
            )

            body = get_email_body(
                payload
            )

            if not body:
                continue

            body = body[:8000]

            context_parts.append(
                f"From: {sender}\n"
                f"Subject: {subject}\n"
                f"Message:\n{body}"
            )

        return "\n\n"
        + "\n\n--- PREVIOUS THREAD MESSAGE ---\n\n".join(
            context_parts
        )

    except Exception as error:

        print(
            f"⚠️ Could not load thread context: {error}"
        )

        return ""


# ============================================================
# GENERATE 3 AI REPLY OPTIONS
# ============================================================

def generate_ai_replies(
    gemini_client,
    email,
    thread_context=""
):
    """
    Generate exactly three professional reply options.

    Gemini is instructed not to invent facts or commitments.
    """

    sender = email.get(
        "sender",
        ""
    )

    subject = email.get(
        "subject",
        ""
    )

    body = email.get(
        "body",
        ""
    )

    links = email.get(
        "links",
        []
    )

    attachments = email.get(
        "attachments",
        []
    )

    analysis = analyze_email(
        email
    )

    attachment_text = "\n".join(
        [
            f"- {item.get('filename', 'Unknown')}"
            for item in attachments
        ]
    )

    if not attachment_text:
        attachment_text = "None"

    links_text = "\n".join(
        [
            f"- {link}"
            for link in links[:3]
        ]
    )

    if not links_text:
        links_text = "None"

    prompt = f"""
You are an expert professional business email assistant.

Write EXACTLY THREE distinct reply options to the client email, using ONLY the information provided in the email and conversation context. Each reply should have an appropriate and good length based on the content and complexity of the email.

RULES:

1. Never invent or assume facts, dates, prices, approvals, deliverables, meetings, promises, or commitments.
2. If requested information is unavailable, acknowledge it politely without making up an answer.
3. Directly address the sender's request and preserve relevant names, dates, requirements, and questions.
4. Keep replies natural, respectful, professional, and suitable for a business/client relationship.
5. Do not mention AI, repeat the full original email, add a fake signature, or invent a job title.
6. Normally write a complete email in 4–8 meaningful paragraphs. Adjust length to the email: simple requests can be shorter; complex responses may require 6–7+ paragraphs.
7. Do not add filler just to increase length. Every paragraph should contribute relevant information.
8. Follow a natural flow: acknowledge → address the request → provide available information/clarification → professional closing.
9. Make each version genuinely different while keeping the facts and meaning accurate.

STYLE 1 — Professional:
Polished, formal, structured, and business-appropriate.

STYLE 2 — Warm & Professional:
Friendly, helpful, respectful, and professional.

STYLE 3 — Concise:
Direct, clear, and professional with minimal unnecessary text.

RETURN ONLY VALID JSON in this exact structure:

{{
  "professional": "full email reply",
  "warm_professional": "full email reply",
  "concise": "full email reply"
}}

CLIENT EMAIL
============
From: {sender}
Subject: {subject}

Body:
{body[:12000]}

EMAIL ANALYSIS
==============
Summary: {analysis.get('summary', '')}
Priority: {analysis.get('priority', 'NORMAL')}
Action: {analysis.get('action', 'None')}

LINKS
=====
{links_text}

ATTACHMENTS
===========
{attachment_text}

CONVERSATION CONTEXT
====================
{thread_context[:30000]}
"""

    try:

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        response_text = (
            response.text
            if response
            else ""
        )

        if not response_text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        # Remove accidental Markdown code fences.
        response_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            response_text.strip(),
            flags=re.IGNORECASE
        )

        response_text = re.sub(
            r"\s*```$",
            "",
            response_text.strip()
        )

        data = json.loads(
            response_text
        )

        replies = [
            data.get(
                "professional",
                ""
            ).strip(),
            data.get(
                "warm_professional",
                ""
            ).strip(),
            data.get(
                "concise",
                ""
            ).strip()
        ]

        if any(
            not reply
            for reply in replies
        ):
            raise ValueError(
                "Gemini did not return all three reply options."
            )

        return replies

    except json.JSONDecodeError as error:

        print(
            "\n❌ Gemini returned invalid JSON."
        )

        print(
            f"Details: {error}"
        )

        return []

    except Exception as error:

        print(
            f"\n❌ Could not generate AI replies: {error}"
        )

        return []


# ============================================================
# DISPLAY REPLY OPTIONS
# ============================================================

def display_reply_options(replies):

    print("\n")
    print("=" * 70)
    print("✨ AI GENERATED EMAIL REPLIES")
    print("=" * 70)

    labels = [
        "OPTION 1 — PROFESSIONAL",
        "OPTION 2 — WARM & PROFESSIONAL",
        "OPTION 3 — CONCISE"
    ]

    for index, reply in enumerate(
        replies
    ):

        print("\n")
        print("-" * 70)
        print(
            labels[index]
        )
        print("-" * 70)
        print(reply)
        print("-" * 70)


# ============================================================
# EDIT SELECTED REPLY
# ============================================================

def edit_reply(reply):
    """
    Let the user optionally edit the selected AI reply before
    it is sent to the client.
    """

    print("\n")
    print("=" * 70)
    print("✏️ EDIT REPLY")
    print("=" * 70)

    print(
        "\nCurrent reply:\n"
    )

    print(reply)

    print("\n")
    print(
        "Press ENTER without typing anything to keep the "
        "generated reply."
    )

    choice = input(
        "\nDo you want to edit it? (y/n): "
    ).strip().lower()

    if choice != "y":
        return reply

    print(
        "\nEnter the complete edited email."
    )

    print(
        "Type END on a new line when finished:\n"
    )

    lines = []

    while True:

        line = input()

        if line.strip() == "END":
            break

        lines.append(
            line
        )

    edited = "\n".join(
        lines
    ).strip()

    if not edited:
        print(
            "⚠️ Empty reply entered. Keeping the AI reply."
        )

        return reply

    return edited


# ============================================================
# SEND GMAIL REPLY
# ============================================================

def send_gmail_reply(
    read_service,
    send_service,
    email_id,
    reply_text
):
    """
    Send the selected reply as a proper Gmail threaded reply.
    """

    try:

        original = get_full_email_for_reply(
            read_service,
            email_id
        )

        payload = original.get(
            "payload",
            {}
        )

        original_sender = get_header_value(
            payload,
            "From"
        )

        original_message_id = get_header_value(
            payload,
            "Message-ID"
        )

        original_references = get_header_value(
            payload,
            "References"
        )

        thread_id = original.get(
            "threadId"
        )

        recipient = parseaddr(
            original_sender
        )[1]

        if not recipient:

            raise ValueError(
                "Could not determine the client's email address."
            )

        original_subject = get_header_value(
            payload,
            "Subject"
        )

        if original_subject.lower().startswith(
            "re:"
        ):

            reply_subject = original_subject

        else:

            reply_subject = (
                "Re: "
                + original_subject
            )

        message = EmailMessage()

        message["To"] = recipient

        message["Subject"] = reply_subject

        if original_message_id:

            message["In-Reply-To"] = (
                original_message_id
            )

        references = original_references.strip()

        if original_message_id:

            if references:

                references = (
                    references
                    + " "
                    + original_message_id
                )

            else:

                references = (
                    original_message_id
                )

            message["References"] = references

        message.set_content(
            reply_text
        )

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode(
            "utf-8"
        )

        body = {
            "raw": encoded_message
        }

        if thread_id:

            body["threadId"] = thread_id

        sent = (
            send_service.users()
            .messages()
            .send(
                userId="me",
                body=body
            )
            .execute()
        )

        return {
            "success": True,
            "message_id": sent.get(
                "id",
                ""
            ),
            "recipient": recipient
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }


# ============================================================
# SELECT EMAIL FOR REPLY
# ============================================================

def choose_email_for_reply(
    service,
    max_results=50
):
    """
    Show emails grouped by priority and let the user choose one.
    """

    emails = get_emails(
        service,
        max_results
    )

    if not emails:

        print(
            "\n❌ No emails found."
        )

        return None

    # --------------------------------------------------------
    # Group emails by the existing priority analysis
    # --------------------------------------------------------

    important_emails = []
    normal_emails = []
    low_emails = []

    for email in emails:

        priority = analyze_email(
            email
        ).get(
            "priority",
            "NORMAL"
        )

        if priority == "IMPORTANT":

            important_emails.append(
                email
            )

        elif priority == "LOW":

            low_emails.append(
                email
            )

        else:

            normal_emails.append(
                email
            )

    categories = {
        "1": ("🔴 IMPORTANT EMAILS", important_emails),
        "2": ("🟡 NORMAL EMAILS", normal_emails),
        "3": ("⚪ LOW EMAILS", low_emails)
    }

    while True:

        print("\n")
        print("=" * 80)
        print("📨 SELECT EMAIL CATEGORY")
        print("=" * 80)

        print(
            f"\n[1] 🔴 IMPORTANT EMAILS ({len(important_emails)})"
        )

        print(
            f"[2] 🟡 NORMAL EMAILS    ({len(normal_emails)})"
        )

        print(
            f"[3] ⚪ LOW EMAILS        ({len(low_emails)})"
        )

        print(
            "\n[0] Cancel"
        )

        category_choice = input(
            "\nSelect category: "
        ).strip()

        if category_choice == "0":

            return None

        if category_choice not in categories:

            print(
                "❌ Please select 1, 2, or 3."
            )

            continue

        category_name, selected_emails = categories[
            category_choice
        ]

        if not selected_emails:

            print(
                f"\n❌ No emails available in {category_name}."
            )

            continue

        print("\n")
        print("=" * 80)
        print(
            f"📨 {category_name}"
        )
        print("=" * 80)

        for index, email in enumerate(
            selected_emails,
            start=1
        ):

            sender = email.get(
                "sender",
                "(Unknown)"
            )

            subject = email.get(
                "subject",
                "(No Subject)"
            )

            summary = create_clean_summary(
                email.get(
                    "body",
                    ""
                )
            )

            print(
                f"\n[{index}] "
                f"{subject}"
            )

            print(
                f"    From: {sender}"
            )

            print(
                f"    {summary[:160]}"
            )

        print("\n")
        print("[0] Back to categories")

        while True:

            choice = input(
                "\nEnter email number: "
            ).strip()

            if choice == "0":

                break

            try:

                index = int(
                    choice
                )

            except ValueError:

                print(
                    "❌ Please enter a valid number."
                )

                continue

            if 1 <= index <= len(selected_emails):

                return selected_emails[
                    index - 1
                ]

            print(
                "❌ Invalid email number."
            )


# ============================================================
# AI REPLY WORKFLOW
# ============================================================

def ai_reply_workflow(
    read_service,
    send_service,
    gemini_client
):
    """
    Complete terminal workflow:

    Select email
        ↓
    Read thread context
        ↓
    Generate 3 replies
        ↓
    Select reply
        ↓
    Edit if desired
        ↓
    Confirm
        ↓
    Send through Gmail
    """

    email = choose_email_for_reply(
        read_service
    )

    if not email:
        return

    print("\n")
    print("=" * 70)
    print("📧 SELECTED EMAIL")
    print("=" * 70)

    print(
        f"From    : {email.get('sender', '')}"
    )

    print(
        f"Subject : {email.get('subject', '')}"
    )

    print(
        f"\nMessage:\n{email.get('body', '')[:6000]}"
    )

    print("\n")
    print(
        "🧠 Loading conversation context..."
    )

    thread_context = get_thread_context(
        read_service,
        email["id"]
    )

    print(
        "✨ Generating 3 professional replies..."
    )

    replies = generate_ai_replies(
        gemini_client,
        email,
        thread_context
    )

    if len(replies) != 3:

        print(
            "\n❌ Reply generation failed."
        )

        return

    display_reply_options(
        replies
    )

    while True:

        choice = input(
            "\nSelect reply (1/2/3) or 0 to cancel: "
        ).strip()

        if choice == "0":
            print(
                "\n❌ Reply cancelled."
            )
            return

        if choice in (
            "1",
            "2",
            "3"
        ):
            break

        print(
            "❌ Please select 1, 2, or 3."
        )

    selected_reply = replies[
        int(choice) - 1
    ]

    selected_reply = edit_reply(
        selected_reply
    )

    print("\n")
    print("=" * 70)
    print("📤 FINAL EMAIL")
    print("=" * 70)

    print(
        selected_reply
    )

    print("\n")

    confirm = input(
        "Send this reply to the client? (yes/no): "
    ).strip().lower()

    if confirm not in (
        "yes",
        "y"
    ):

        print(
            "\n❌ Email was not sent."
        )

        return

    print(
        "\n📨 Sending reply through Gmail..."
    )

    result = send_gmail_reply(
        read_service,
        send_service,
        email["id"],
        selected_reply
    )

    if result.get(
        "success"
    ):

        print("\n")
        print("=" * 70)
        print("✅ REPLY SENT SUCCESSFULLY")
        print("=" * 70)

        print(
            f"Recipient: {result.get('recipient', '')}"
        )

        print(
            f"Message ID: {result.get('message_id', '')}"
        )

        print(
            "The reply was sent as a Gmail thread reply."
        )

    else:

        print("\n")
        print("=" * 70)
        print("❌ FAILED TO SEND REPLY")
        print("=" * 70)

        print(
            result.get(
                "error",
                "Unknown Gmail error."
            )
        )


# ============================================================
# TERMINAL AI REPLY MENU
# ============================================================

def ai_reply_terminal_menu(
    read_service
):
    """
    Terminal menu for the AI reply feature.

    The existing email-monitoring system is not removed.
    After leaving this menu, the original continuous monitor
    can still be started.
    """

    print("\n")
    print("=" * 70)
    print("🤖 AI EMAIL REPLY ASSISTANT")
    print("=" * 70)

    print(
        "\nThis feature lets you:"
    )

    print(
        "  1. Select a Gmail email"
    )

    print(
        "  2. Generate 3 AI reply versions"
    )

    print(
        "  3. Select one"
    )

    print(
        "  4. Edit it if needed"
    )

    print(
        "  5. Confirm before sending"
    )

    print(
        "  6. Send it as a Gmail thread reply"
    )

    print(
        "\nCommands:"
    )

    print(
        "  R = Generate a reply"
    )

    print(
        "  Q = Exit AI reply assistant"
    )

    try:

        gemini_client = get_gemini_client()

    except Exception as error:

        print(
            f"\n❌ Gemini setup failed: {error}"
        )

        return

    try:

        send_service = gmail_send_login()

    except Exception as error:

        print(
            f"\n❌ Gmail send authorization failed: {error}"
        )

        return

    while True:

        command = input(
            "\nAI Reply > "
        ).strip().lower()

        if command == "q":

            print(
                "\n↩️ Leaving AI reply assistant."
            )

            break

        if command == "r" or command == "":

            ai_reply_workflow(
                read_service,
                send_service,
                gemini_client
            )

            continue

        print(
            "❌ Unknown command. Use R or Q."
        )


# ============================================================
# NEW MAIN ENTRY POINT
# ============================================================
#
# IMPORTANT:
# The original main() function above is unchanged.
# This wrapper reuses the same Gmail login, notes processing
# and monitoring functions, and adds the AI reply terminal menu.
# ============================================================

def main_with_ai_reply():

    print("\n")
    print("=" * 60)

    print(
        "📧 EMAIL INTELLIGENCE ASSISTANT"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Original Gmail login
    # --------------------------------------------------------

    service = gmail_login()

    # --------------------------------------------------------
    # Original notes rebuilding
    # --------------------------------------------------------

    if os.path.exists(
        NOTES_FILE
    ):

        print(
            "\n🧹 Rebuilding email_notes.txt "
            "using the new structure..."
        )

        os.remove(
            NOTES_FILE
        )

    initialize_notes_file()

    # --------------------------------------------------------
    # Original recent email processing
    # --------------------------------------------------------

    initialize_recent_emails(
        service
    )

    # --------------------------------------------------------
    # NEW AI REPLY FEATURE
    # --------------------------------------------------------

    ai_reply_terminal_menu(
        service
    )

    # --------------------------------------------------------
    # Original continuous monitor
    # --------------------------------------------------------

    monitor_emails(
        service
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main_with_ai_reply()