# canvas_sync/state.py
from __future__ import annotations

import json
import os
from typing import Optional


class SyncState:
    def __init__(self, path: str):
        self._path = path
        self._data: dict = {}
        if os.path.exists(path):
            with open(path) as f:
                self._data = json.load(f)

    def get_week(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    def set_week(self, key: str, value: dict) -> None:
        self._data[key] = value

    def all_weeks(self) -> dict:
        return dict(self._data)

    def save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)
