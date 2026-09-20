# Export action items to Markdown notes

Use this recipe to export Omi tasks and follow-ups to Markdown checklists for Obsidian, Notion, Logseq, or personal daily logs. It reads a saved JSON export, creates native Markdown checkboxes (`- [ ]` and `- [x]`), and structures the note with YAML frontmatter.

You need Python 3.10+ and an authenticated `omi-cli`.

## 1. Export action items from Omi

Export all action items to JSON:

```sh
omi --json action-item list > action_items.json
```

Or pipe directly from `omi-cli`:

```sh
omi --json action-item list | python action_items_to_markdown.py - --output ~/vault/Tasks.md
```

## 2. Options and Filtering

### Filter by completion status

Export only open (uncompleted) tasks:

```sh
omi --json action-item list | python action_items_to_markdown.py - --status open -o ~/vault/OpenTasks.md
```

Export only completed tasks:

```sh
omi --json action-item list | python action_items_to_markdown.py - --status completed -o ~/vault/CompletedTasks.md
```

### Grouping options

* `--group-by status` (default): Groups items under `## ⏳ Open Tasks` and `## ✅ Completed Tasks`.
* `--group-by date`: Groups tasks chronologically by due date (`## 📅 YYYY-MM-DD`).
* `--group-by none`: Renders a simple flat list.

## 3. Obsidian & Second-Brain Integration

Each generated note contains YAML frontmatter:

```yaml
---
type: omi-action-items
total: 8
open_count: 5
completed_count: 3
exported_at: "2026-09-20T10:45:00+00:00"
tags:
  - omi
  - tasks
  - action-items
---
```

This enables seamless querying with the **Obsidian Dataview** plugin:

```dataview
TASK
FROM "Tasks"
WHERE !completed
```
