"""Unit tests for action_items_to_markdown recipe."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

script_path = Path(__file__).resolve().parent.parent / "examples" / "action_items_to_markdown.py"
spec = importlib.util.spec_from_file_location("action_items_to_markdown", script_path)
a2m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a2m)


class TestActionItemsToMarkdown(unittest.TestCase):
    def test_markdown_checkboxes_and_metadata(self):
        items = [
            {
                "id": "12345678",
                "completed": False,
                "description": "Prepare slides for meeting",
                "due_at": "2026-09-25T14:00:00Z",
                "created_at": "2026-09-20T10:00:00Z",
                "conversation_id": "conv-98765432",
            },
            {
                "id": "87654321",
                "completed": True,
                "description": "Review pull request",
                "due_at": None,
                "created_at": "2026-09-19T09:00:00Z",
            },
        ]

        doc = a2m.action_items_to_markdown(items, group_by="status")

        # Verify YAML frontmatter counts
        self.assertIn("type: omi-action-items", doc)
        self.assertIn("total: 2", doc)
        self.assertIn("open_count: 1", doc)
        self.assertIn("completed_count: 1", doc)

        # Verify checkboxes
        self.assertIn("- [ ] Prepare slides for meeting", doc)
        self.assertIn("- [x] Review pull request", doc)

        # Verify metadata rendering
        self.assertIn("⏰ due: `2026-09-25`", doc)
        self.assertIn("💬 `conv:conv-987`", doc)
        self.assertIn("`#12345678`", doc)

    def test_group_by_status(self):
        items = [
            {"id": "1", "completed": False, "description": "Active task"},
            {"id": "2", "completed": True, "description": "Done task"},
        ]
        doc = a2m.action_items_to_markdown(items, group_by="status")
        self.assertIn("## ⏳ Open Tasks", doc)
        self.assertIn("## ✅ Completed Tasks", doc)

    def test_group_by_date(self):
        items = [
            {"id": "1", "completed": False, "description": "Task 1", "due_at": "2026-09-25T10:00:00Z"},
            {"id": "2", "completed": False, "description": "Task 2", "due_at": "2026-09-28T10:00:00Z"},
        ]
        doc = a2m.action_items_to_markdown(items, group_by="date")
        self.assertIn("## 📅 2026-09-25", doc)
        self.assertIn("## 📅 2026-09-28", doc)

    def test_filter_action_items(self):
        items = [
            {"id": "1", "completed": False, "description": "Open"},
            {"id": "2", "completed": True, "description": "Done"},
        ]
        open_only = a2m.filter_action_items(items, status_filter="open")
        self.assertEqual(len(open_only), 1)
        self.assertEqual(open_only[0]["description"], "Open")

        done_only = a2m.filter_action_items(items, status_filter="completed")
        self.assertEqual(len(done_only), 1)
        self.assertEqual(done_only[0]["description"], "Done")

    def test_empty_items(self):
        doc = a2m.action_items_to_markdown([])
        self.assertIn("total: 0", doc)
        self.assertIn("_No action items found matching criteria._", doc)


if __name__ == "__main__":
    unittest.main()
