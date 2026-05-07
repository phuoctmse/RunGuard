"""Markdown runbook parser — extracts sections from Markdown."""

from typing import Any


def parse_runbook_markdown(markdown: str) -> dict[str, Any]:
    """Parse a Markdown runbook into sections.

    Returns a dict with keys: scope, allowed_tools, forbidden_tools,
    severity, rollback_steps, title.
    """
    sections: dict[str, Any] = {}
    current_section = None
    lines = markdown.strip().split("\n")

    # Extract title (first H1)
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            sections["title"] = line[2:].strip()
            break

    for line in lines:
        stripped = line.strip()

        # Detect H2 section headers
        if stripped.startswith("## "):
            section_name = stripped[3:].strip().lower().replace(" ", "_")
            current_section = section_name
            sections[current_section] = []
            continue

        # Parse list items
        if stripped.startswith("- ") and current_section:
            item = stripped[2:].strip()
            sections[current_section].append(item)
            continue

        # Parse numbered list items (for rollback steps)
        if current_section and stripped and stripped[0].isdigit():
            dot_pos = stripped.find(". ")
            if dot_pos > 0 and stripped[:dot_pos].isdigit():
                sections[current_section].append(stripped[dot_pos + 2 :].strip())
                continue

        # Severity is a plain text line (not a list)
        if current_section == "severity" and stripped and not stripped.startswith("-"):
            sections["severity"] = stripped

    # Convert severity from list to string if needed
    if isinstance(sections.get("severity"), list):
        severity_list = sections["severity"]
        sections["severity"] = severity_list[0] if severity_list else "medium"

    # Parse scope into structured format
    if "scope" in sections and isinstance(sections["scope"], list):
        scope: dict[str, list[str]] = {
            "namespaces": [],
            "workloads": [],
        }
        for item in sections["scope"]:
            if item.lower().startswith("namespaces:"):
                values = item.split(":", 1)[1]
                scope["namespaces"] = [v.strip() for v in values.split(",")]
            elif item.lower().startswith("workloads:"):
                values = item.split(":", 1)[1]
                scope["workloads"] = [v.strip() for v in values.split(",")]
        sections["scope"] = scope

    return sections
