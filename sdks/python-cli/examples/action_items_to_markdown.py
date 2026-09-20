"""
Convert Omi action items JSON exports to clean Markdown task lists for Obsidian, Notion, Logseq, and daily notes.

Usage:
    # Pipe directly from omi CLI
    omi --json action-item list | python action_items_to_markdown.py -

    # Export to a specific Markdown file (single note)
    omi --json action-item list | python action_items_to_markdown.py - --output ~/vault/Tasks.md

    # Export into separate status-based notes in a directory
    python action_items_to_markdown.py action_items.json --output-dir ./vault/tasks/ --group-by status

    # Export only open items
    omi --json action-item list | python action_items_to_markdown.py - --status open
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_datetime(iso_str: Optional[str]) -> Optional[datetime]:
    """Safely parse an ISO-8601 datetime string and normalize to UTC."""
    if not iso_str or not isinstance(iso_str, str):
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def format_action_item(item: Dict[str, Any], include_metadata: bool = True) -> str:
    """Format a single action item as a Markdown checklist item."""
    desc = str(item.get("description") or "").strip().replace("\r\n", " ").replace("\n", " ")
    if not desc:
        desc = "_Untitled action item_"

    is_completed = bool(item.get("completed", False))
    box = "- [x]" if is_completed else "- [ ]"

    parts = [f"{box} {desc}"]

    if include_metadata:
        meta_tags: List[str] = []

        due_dt = parse_datetime(item.get("due_at"))
        if due_dt:
            meta_tags.append(f"⏰ due: `{due_dt.strftime('%Y-%m-%d')}`")

        created_dt = parse_datetime(item.get("created_at"))
        if created_dt:
            meta_tags.append(f"📅 created: `{created_dt.strftime('%Y-%m-%d')}`")

        conv_id = item.get("conversation_id")
        if conv_id:
            safe_conv = re.sub(r"[^\w-]", "", str(conv_id))[:8]
            if safe_conv:
                meta_tags.append(f"💬 `conv:{safe_conv}`")

        item_id = item.get("id")
        if item_id:
            safe_id = re.sub(r"[^\w-]", "", str(item_id))[:8]
            if safe_id:
                meta_tags.append(f"`#{safe_id}`")

        if meta_tags:
            parts.append(f"  *({' · '.join(meta_tags)})*")

    return "\n".join(parts)


def action_items_to_markdown(
    items: List[Dict[str, Any]],
    title: str = "Omi Action Items & Tasks",
    group_by: str = "status",
) -> str:
    """Render a list of action items into a structured Markdown note with YAML frontmatter."""
    total = len(items)
    open_count = sum(1 for it in items if not it.get("completed"))
    completed_count = total - open_count

    now_iso = datetime.now(timezone.utc).isoformat()

    lines: List[str] = [
        "---",
        "type: omi-action-items",
        f"total: {total}",
        f"open_count: {open_count}",
        f"completed_count: {completed_count}",
        f"exported_at: {json.dumps(now_iso)}",
        "tags:",
        "  - omi",
        "  - tasks",
        "  - action-items",
        "---",
        "",
        f"# {title}",
        "",
        f"> **Summary:** {open_count} open, {completed_count} completed ({total} total). Exported from Omi CLI.",
        "",
    ]

    if not items:
        lines.append("_No action items found matching criteria._")
        lines.append("")
        return "\n".join(lines)

    if group_by == "status":
        open_items = [it for it in items if not it.get("completed")]
        completed_items = [it for it in items if it.get("completed")]

        if open_items:
            lines.append("## ⏳ Open Tasks")
            lines.append("")
            for it in open_items:
                lines.append(format_action_item(it))
            lines.append("")

        if completed_items:
            lines.append("## ✅ Completed Tasks")
            lines.append("")
            for it in completed_items:
                lines.append(format_action_item(it))
            lines.append("")

    elif group_by == "date":
        date_groups: Dict[str, List[Dict[str, Any]]] = {}
        for it in items:
            due_dt = parse_datetime(it.get("due_at")) or parse_datetime(it.get("created_at"))
            key = due_dt.strftime("%Y-%m-%d") if due_dt else "No Date"
            date_groups.setdefault(key, []).append(it)

        for date_key in sorted(date_groups.keys()):
            lines.append(f"## 📅 {date_key}")
            lines.append("")
            for it in date_groups[date_key]:
                lines.append(format_action_item(it))
            lines.append("")

    else:
        for it in items:
            lines.append(format_action_item(it))
        lines.append("")

    return "\n".join(lines)


def filter_action_items(
    items: List[Dict[str, Any]],
    status_filter: str = "all",
) -> List[Dict[str, Any]]:
    """Filter action items by status."""
    if status_filter == "open":
        return [it for it in items if not it.get("completed")]
    if status_filter == "completed":
        return [it for it in items if it.get("completed")]
    return items


def parse_input_payload(raw_data: str) -> List[Dict[str, Any]]:
    """Parse JSON array or nested object from CLI output."""
    payload = json.loads(raw_data)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return (
            payload.get("action_items")
            or payload.get("items")
            or payload.get("data")
            or [payload]
        )
    raise ValueError("Input must be a JSON array or object containing action items.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Omi action items JSON exports to clean Markdown task lists."
    )
    parser.add_argument(
        "input",
        help="Path to JSON file containing action items, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output Markdown file path. Defaults to stdout.",
    )
    parser.add_argument(
        "--status",
        "-s",
        choices=["all", "open", "completed"],
        default="all",
        help="Filter action items by status (default: all).",
    )
    parser.add_argument(
        "--group-by",
        "-g",
        choices=["status", "date", "none"],
        default="status",
        help="Grouping strategy for checklist (default: status).",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        default="Omi Action Items & Tasks",
        help="Custom header title for the document.",
    )

    args = parser.parse_args()

    try:
        if args.input == "-":
            raw_data = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
        else:
            input_path = Path(args.input)
            if not input_path.exists():
                sys.stderr.write(f"Error: Input file does not exist: {args.input}\n")
                return 1
            raw_data = input_path.read_bytes().decode("utf-8-sig", errors="replace")

        if not raw_data.strip():
            sys.stderr.write("Error: Input payload is empty.\n")
            return 1

        raw_items = parse_input_payload(raw_data)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Error: Invalid JSON input: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"Error reading input: {exc}\n")
        return 1

    items = filter_action_items(raw_items, status_filter=args.status)
    markdown_doc = action_items_to_markdown(items, title=args.title, group_by=args.group_by)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown_doc, encoding="utf-8")
        sys.stderr.write(f"Successfully exported {len(items)} action items to {args.output}\n")
    else:
        try:
            sys.stdout.write(markdown_doc)
        except UnicodeEncodeError:
            sys.stdout.buffer.write(markdown_doc.encode("utf-8", errors="replace"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
