#!/usr/bin/env python3
"""Convert the claude-history (v1) SQLite database into a conversations.json
that the claude-history-2 static viewer (index.html) can open.

v1 parsed your real Claude.ai export into claude-history/data/conversations.db.
This script reshapes that into the native-export-style JSON the viewer expects:
a top-level array of conversations, each with `name`, `created_at`, `updated_at`,
and a `chat_messages` array of {sender, created_at, text} turns.

The viewer renders `text` as markdown when no typed `content` array is present,
so the prompt/response text comes through with its code blocks and formatting.

Usage:
    python3 scripts/convert-history.py        # or: npm run convert-history

Output goes to data-claude-history/conversations.json, which matches this repo's
`data-*` .gitignore rule and is therefore never committed. Open that file in the
viewer via the "Open conversations.json" button (your data stays on your machine).
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "claude-history" / "data" / "conversations.db"
OUT_PATH = ROOT / "data-claude-history" / "conversations.json"


def main() -> int:
    if not DB_PATH.exists():
        print(f"error: database not found at {DB_PATH}", file=sys.stderr)
        print(
            "Generate it first from the v1 project:\n"
            "  cd claude-history && uv run python main.py parse",
            file=sys.stderr,
        )
        return 1

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    convs = con.execute(
        "SELECT id, title, created, updated FROM conversations ORDER BY updated DESC"
    ).fetchall()

    out = []
    message_count = 0
    for c in convs:
        turns = con.execute(
            "SELECT role, timestamp, text FROM turns "
            "WHERE conversation_id = ? ORDER BY id",
            (c["id"],),
        ).fetchall()

        messages = []
        for i, t in enumerate(turns):
            messages.append(
                {
                    "uuid": f"{c['id']}-{i}",
                    "sender": "human" if t["role"] == "prompt" else "assistant",
                    "created_at": t["timestamp"] or "",
                    "text": t["text"] or "",
                }
            )
        message_count += len(messages)

        out.append(
            {
                "uuid": c["id"],
                "name": c["title"] or "(untitled)",
                "created_at": c["created"] or "",
                "updated_at": c["updated"] or "",
                "chat_messages": messages,
            }
        )

    con.close()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rel = OUT_PATH.relative_to(ROOT)
    print(f"Wrote {len(out)} conversations ({message_count} messages) -> {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
