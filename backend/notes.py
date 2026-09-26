"""Persistent email notes and monitoring operations."""

from .email_backend import (
    add_note_to_top,
    create_note,
    get_saved_email_ids,
    initialize_notes_file,
    initialize_recent_emails,
    monitor_emails,
    process_new_email,
    update_email_priority_counts,
)

__all__ = [
    "add_note_to_top",
    "create_note",
    "get_saved_email_ids",
    "initialize_notes_file",
    "initialize_recent_emails",
    "monitor_emails",
    "process_new_email",
    "update_email_priority_counts",
]
