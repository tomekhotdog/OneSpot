from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable

from filelock import FileLock

from backend.config import STATE_FILE_PATH
from backend.models import AppState


class StateManager:
    def __init__(self, path: Path | None = None):
        self.path = path or STATE_FILE_PATH
        self.lock_path = self.path.with_suffix(".lock")
        self._lock = FileLock(str(self.lock_path))

    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> AppState:
        self._ensure_dir()
        if not self.path.exists():
            return AppState()
        with self._lock:
            data = json.loads(self.path.read_text())
        return AppState.model_validate(data)

    def write(self, state: AppState) -> None:
        self._ensure_dir()
        with self._lock:
            # Backup current state
            if self.path.exists():
                backup_path = self.path.with_name("state.backup.json")
                backup_path.write_text(self.path.read_text())
            # Atomic write via temp file
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self.path.parent), suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(state.model_dump(mode="json"), f, indent=2, default=str)
                os.replace(tmp_path, str(self.path))
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

    def update(self, fn: Callable[[AppState], AppState]) -> AppState:
        """Read state, apply fn, write back. Returns the new state."""
        self._ensure_dir()
        with self._lock:
            state = self._read_unlocked()
            new_state = fn(state)
            self._write_unlocked(new_state)
        return new_state

    def _read_unlocked(self) -> AppState:
        if not self.path.exists():
            return AppState()
        data = json.loads(self.path.read_text())
        return AppState.model_validate(data)

    def _write_unlocked(self, state: AppState) -> None:
        if self.path.exists():
            backup_path = self.path.with_name("state.backup.json")
            backup_path.write_text(self.path.read_text())
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state.model_dump(mode="json"), f, indent=2, default=str)
            os.replace(tmp_path, str(self.path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


# Singleton instance
state_manager = StateManager()
