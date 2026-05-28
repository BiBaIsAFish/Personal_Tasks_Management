from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TASK_FIELDS = ("title", "start_time", "end_time", "tags", "priority", "status", "notes")
OPTIONAL_FIELDS = ("tags", "priority", "status", "notes")

DEFAULT_DRAFT_PATH = Path(__file__).resolve().parents[1] / "run_bot" / "task_draft.json"

DEFAULT_DOCUMENT: dict[str, Any] = {
    "_comment": "Runtime draft for the next Notion task. Keep this file as valid JSON; comments are stored in _comment fields.",
    "required_fields": ["title", "start_time", "end_time"],
    "optional_fields": list(OPTIONAL_FIELDS),
    "template": {
        "_comment": "Fill required fields before creating a Notion task. Optional fields may stay empty.",
        "title": "",
        "start_time": "",
        "end_time": "",
        "tags": [],
        "priority": "",
        "status": "",
        "notes": "",
    },
    "draft": None,
}


class JsonTaskDraftStore:
    def __init__(self, path: str | Path = DEFAULT_DRAFT_PATH) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._fresh_document()
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_draft(self, arguments: dict[str, Any]) -> None:
        document = self.load()
        draft = {field: self._default_value(field) for field in TASK_FIELDS}
        for field in TASK_FIELDS:
            if field in arguments and arguments[field] is not None:
                draft[field] = arguments[field]
        document["draft"] = draft
        self._write(document)

    def clear_draft(self) -> None:
        document = self.load()
        document["draft"] = None
        self._write(document)

    def ensure_template(self) -> None:
        if not self.path.exists():
            self._write(self._fresh_document())

    def _fresh_document(self) -> dict[str, Any]:
        return json.loads(json.dumps(DEFAULT_DOCUMENT))

    def _write(self, document: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _default_value(self, field: str) -> Any:
        return [] if field == "tags" else ""
