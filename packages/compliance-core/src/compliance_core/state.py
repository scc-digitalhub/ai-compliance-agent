# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Workspace and in-memory state stores shared by runtime adapters."""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Any, Mapping, Protocol

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None
    import msvcrt


# The flat keys hold the active project's analyses; other projects are kept in WORKSPACES_KEY.
PROJECT_KEY = "analysis_project"
CONTEXT_KEY = "analysis_project_context"
DATASETS_KEY = "analysis_datasets"
MODELS_KEY = "analysis_models"
PROVENANCE_KEY = "analysis_provenance"
ACTIVE_KEY = "analysis_active_project"
WORKSPACES_KEY = "analysis_workspaces"
ENTITIES_KEY = "dh_entities"
REVISIONS_KEY = "dh_spec_revisions"
CODES_KEY = "evaluation_codes"
REPORTS_KEY = "evaluation_reports"

SCOPED_KEYS = (PROJECT_KEY, CONTEXT_KEY, DATASETS_KEY, MODELS_KEY, PROVENANCE_KEY, CODES_KEY, REPORTS_KEY)
_EMPTY: dict[str, Any] = {
    PROJECT_KEY: None, CONTEXT_KEY: None, DATASETS_KEY: {}, MODELS_KEY: {},
    PROVENANCE_KEY: {}, CODES_KEY: {}, REPORTS_KEY: {},
}


def _clean(name: Any) -> str | None:
    return name.strip() if isinstance(name, str) and name.strip() else None


def active_project(state: StateStore) -> str | None:
    """Name of the project whose analyses occupy the flat workspace keys."""
    return _clean(state.get(ACTIVE_KEY)) or _clean((state.get(PROJECT_KEY) or {}).get("name"))


def entity_project(state: StateStore, project: str | None) -> str | None:
    """Use a project argument or the project explicitly established in the workspace."""
    return active_project(state) if project is None else _clean(project)


def known_projects(state: StateStore) -> list[str]:
    names = [active_project(state), *(state.get(WORKSPACES_KEY) or {})]
    return list(dict.fromkeys(name for name in names if name))


def _is_active(state: StateStore, project: str | None) -> bool:
    """Whether `project` maps to the flat keys; with no active project they are still unscoped."""
    project, active = _clean(project), active_project(state)
    return project is None or active is None or project == active


def scoped_get(state: StateStore, key: str, project: str | None = None) -> Any:
    """Read a project-scoped workspace value; `None` selects the active project."""
    if _is_active(state, project):
        value = state.get(key)
    else:
        value = (state.get(WORKSPACES_KEY) or {}).get(_clean(project), {}).get(key)
    return _EMPTY[key] if value is None else value


def scoped_set(state: StateStore, key: str, value: Any, project: str | None = None) -> None:
    """Write a project-scoped value; values of inactive projects never reach the flat keys."""
    project = _clean(project)
    if project and active_project(state) is None:
        activate_project(state, project)
    if _is_active(state, project):
        state[key] = value
        return
    workspaces = dict(state.get(WORKSPACES_KEY) or {})
    workspaces[project] = {**workspaces.get(project, {}), key: value}
    state[WORKSPACES_KEY] = workspaces


def scoped_update(state: StateStore, key: str, entry: str, value: Any, project: str | None = None) -> None:
    """Set one entry of a project-scoped mapping such as the datasets of a project."""
    scoped_set(state, key, {**scoped_get(state, key, project), entry: value}, project)


def activate_project(state: StateStore, name: str) -> None:
    """Select the active project, archiving the previous project's analyses.

    Analyses recorded before any project was selected are adopted by the first selected project.
    """
    name = _clean(name)
    if name is None:
        raise ValueError("A project name is required")
    current = active_project(state)
    if current == name:
        if state.get(ACTIVE_KEY) != name:
            state[ACTIVE_KEY] = name
        return
    workspaces = dict(state.get(WORKSPACES_KEY) or {})
    snapshot = {key: state.get(key) for key in SCOPED_KEYS if state.get(key)}
    archived = workspaces.pop(name, {})
    if current:
        if snapshot:
            workspaces[current] = snapshot
        restored = archived
    else:
        restored = {**snapshot, **archived}
        for key in (DATASETS_KEY, MODELS_KEY, PROVENANCE_KEY, CODES_KEY, REPORTS_KEY):
            restored[key] = {**snapshot.get(key, {}), **archived.get(key, {})}
    for key in SCOPED_KEYS:
        value = restored.get(key)
        state[key] = _EMPTY[key] if value is None else value
    state[WORKSPACES_KEY] = workspaces
    state[ACTIVE_KEY] = name


@contextmanager
def transaction(state: StateStore) -> Iterator[None]:
    """Group several state updates atomically when the store supports transactions."""
    begin = getattr(state, "transaction", None)
    if begin is None:
        yield
    else:
        with begin():
            yield


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
    provenance: dict[str, dict[str, Any]] = field(default_factory=dict)
    active_project: str | None = None
    other_projects: dict[str, dict[str, Any]] = field(default_factory=dict)
    evaluation_codes: dict[str, dict[str, Any]] = field(default_factory=dict)
    evaluation_reports: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_store(cls, state: Mapping[str, Any]) -> "ComplianceWorkspace":
        return cls(
            project=state.get(PROJECT_KEY),
            project_context=state.get(CONTEXT_KEY),
            datasets=state.get(DATASETS_KEY) or {},
            models=state.get(MODELS_KEY) or {},
            entities=state.get(ENTITIES_KEY) or {},
            provenance=state.get(PROVENANCE_KEY) or {},
            active_project=state.get(ACTIVE_KEY),
            other_projects=state.get(WORKSPACES_KEY) or {},
            evaluation_codes=state.get(CODES_KEY) or {},
            evaluation_reports=state.get(REPORTS_KEY) or {},
        )

    def write_to(self, state: MutableMapping[str, Any]) -> None:
        state[PROJECT_KEY] = self.project
        state[CONTEXT_KEY] = self.project_context
        state[DATASETS_KEY] = self.datasets
        state[MODELS_KEY] = self.models
        state[ENTITIES_KEY] = self.entities
        state[PROVENANCE_KEY] = self.provenance
        state[ACTIVE_KEY] = self.active_project
        state[WORKSPACES_KEY] = self.other_projects
        state[CODES_KEY] = self.evaluation_codes
        state[REPORTS_KEY] = self.evaluation_reports


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
    """Persist JSON-compatible state in a workspace-local `.compliance` directory.

    Every operation holds an exclusive lock on `state.lock`, so several processes (for example,
    MCP servers launched by different hosts for one workspace) never lose each other's updates.
    Use `transaction()` to make a read-modify-write sequence atomic.
    """

    def __init__(self, directory: str | Path = ".compliance"):
        self.directory = Path(directory).expanduser().resolve()
        self.path = self.directory / "state.json"
        self._lock = RLock()
        self._depth = 0
        self._cache: dict[str, Any] = {}
        self._dirty = False
        self._handle: Any = None

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

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Hold the workspace lock; changes are written once, and discarded on error."""
        with self._lock:
            if self._depth == 0:
                self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                handle = open(self.directory / "state.lock", "a+b")
                try:
                    _lock_file(handle)
                    self._cache, self._dirty = self._read(), False
                except BaseException:
                    handle.close()
                    raise
                self._handle = handle
            self._depth += 1
            succeeded = False
            try:
                yield
                succeeded = True
            finally:
                self._depth -= 1
                if self._depth == 0:
                    try:
                        if succeeded and self._dirty:
                            self._write(self._cache)
                    finally:
                        self._cache, self._dirty = {}, False
                        _unlock_file(self._handle)
                        self._handle.close()
                        self._handle = None

    def __getitem__(self, key: str) -> Any:
        with self.transaction():
            return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        with self.transaction():
            self._cache[key] = value
            self._dirty = True

    def __delitem__(self, key: str) -> None:
        with self.transaction():
            del self._cache[key]
            self._dirty = True

    def __iter__(self) -> Iterator[str]:
        with self.transaction():
            return iter(tuple(self._cache))

    def __len__(self) -> int:
        with self.transaction():
            return len(self._cache)

    def snapshot(self) -> dict[str, Any]:
        with self.transaction():
            return json.loads(json.dumps(self._cache))


def _lock_file(handle: Any) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    else:  # pragma: no cover - Windows
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)


def _unlock_file(handle: Any) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    else:  # pragma: no cover - Windows
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


__all__ = [
    "ACTIVE_KEY",
    "CONTEXT_KEY",
    "DATASETS_KEY",
    "ENTITIES_KEY",
    "PROVENANCE_KEY",
    "REVISIONS_KEY",
    "SCOPED_KEYS",
    "WORKSPACES_KEY",
    "activate_project",
    "active_project",
    "entity_project",
    "known_projects",
    "scoped_get",
    "scoped_set",
    "scoped_update",
    "transaction",
    "FileStateStore",
    "InMemoryStateStore",
    "MappingStateStore",
    "MODELS_KEY",
    "PROJECT_KEY",
    "ComplianceWorkspace",
    "StateStore",
]
