"""Shared email display and grouping helpers."""


def priority(backend, email):
    try:
        return backend.analyze_email(email).get("priority", "NORMAL")
    except Exception:
        return "NORMAL"


def grouped(backend, emails):
    result = {"IMPORTANT": [], "NORMAL": [], "LOW": []}
    for email in emails:
        result.setdefault(priority(backend, email), result["NORMAL"]).append(email)
    return result


def email_label(priority_name):
    return {
        "IMPORTANT": "Important",
        "NORMAL": "Normal",
        "LOW": "Low",
    }.get(priority_name, "Normal")
