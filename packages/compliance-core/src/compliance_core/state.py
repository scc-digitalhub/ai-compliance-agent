"""Workspace and in-memory state stores shared by runtime adapters."""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, Protocol


PROJECT_KEY = "analysis_project"
CONTEXT_KEY = "analysis_project_context"
DATASETS_KEY = "analysis_datasets"
MODELS_KEY = "analysis_models"
ENTITIES_KEY = "dh_entities"


class StateStore(Protocol):
    """Mutable JSON-compatible state exposed to compliance tools."""

    def __getitem__(self, key: str) -> Any: ...

    def __setitem__(self, key: str, value: Any) -> None: ...

    def __delitem__(self, key: str) -> None: ...

    def __iter__(self) -> Iterator[str]: ...

    def __len__(self) -> int: ...

    def get(self, key: str, default: Any = None) -> Any: ...


@dataclass
class ComplianceWorkspace:
    project: dict[str, Any] | None = None
    project_context: dict[str, Any] | None = None
    datasets: dict[str, dict[str, Any]] = field(default_factory=dict)
    models: dict[str, dict[str, Any]] = field(default_factory=dict)
    entities: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)

    @classmethod
    def from_store(cls, state: Mapping[str, Any]) -> "ComplianceWorkspace":
        return cls(
            project=state.get(PROJECT_KEY),
            project_context=state.get(CONTEXT_KEY),
            datasets=state.get(DATASETS_KEY, {}),
            models=state.get(MODELS_KEY, {}),
            entities=state.get(ENTITIES_KEY, {}),
        )

    def write_to(self, state: MutableMapping[str, Any]) -> None:
        state[PROJECT_KEY] = self.project
        state[CONTEXT_KEY] = self.project_context
        state[DATASETS_KEY] = self.datasets
        state[MODELS_KEY] = self.models
        state[ENTITIES_KEY] = self.entities


class InMemoryStateStore(MutableMapping[str, Any]):
    def __init__(self, initial: MutableMapping[str, Any] | None = None):
        self._data = dict(initial or {})

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


class MappingStateStore(MutableMapping[str, Any]):
    """Adapter over a host-provided mutable mapping, such as ADK session state."""

    def __init__(self, mapping: MutableMapping[str, Any]):
        self._mapping = mapping

    def __getitem__(self, key: str) -> Any:
        return self._mapping[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._mapping[key] = value

    def __delitem__(self, key: str) -> None:
        del self._mapping[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)

    def __len__(self) -> int:
        return len(self._mapping)


class FileStateStore(MutableMapping[str, Any]):
    """Persist JSON-compatible state in a workspace-local `.compliance` directory."""

    def __init__(self, directory: str | Path = ".compliance"):
        self.directory = Path(directory).expanduser().resolve()
        self.path = self.directory / "state.json"
        self._lock = RLock()

    def _read(self) -> dict[str, Any]:
        try:
            with self.path.open(encoding="utf-8") as file:
                state = json.load(file)
        except FileNotFoundError:
            return {}
        if not isinstance(state, dict):
            raise ValueError(f"State file must contain a JSON object: {self.path}")
        return state

    def _write(self, state: dict[str, Any]) -> None:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        encoded = json.dumps(state, ensure_ascii=False, indent=2)
        fd, temporary_name = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=self.directory)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                file.write(encoded)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            return self._read()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            state = self._read()
            state[key] = value
            self._write(state)

    def __delitem__(self, key: str) -> None:
        with self._lock:
            state = self._read()
            del state[key]
            self._write(state)

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            return iter(tuple(self._read()))

    def __len__(self) -> int:
        with self._lock:
            return len(self._read())

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._read()


__all__ = [
    "CONTEXT_KEY",
    "DATASETS_KEY",
    "ENTITIES_KEY",
    "FileStateStore",
    "InMemoryStateStore",
    "MappingStateStore",
    "MODELS_KEY",
    "PROJECT_KEY",
    "ComplianceWorkspace",
    "StateStore",
]
