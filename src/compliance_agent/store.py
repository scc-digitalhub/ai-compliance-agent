"""JSON file-based persistence for project, dataset, and model entities."""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EntityStore:
    """CRUD store that persists each entity as an individual JSON file under *root/kind/*."""

    def __init__(self, root: Path, kind: str) -> None:
        self._dir = root / kind
        self._dir.mkdir(parents=True, exist_ok=True)
        logger.debug("EntityStore ready at %s", self._dir)

    def _path(self, entity_id: str) -> Path:
        return self._dir / f"{entity_id}.json"

    def create(self, data: dict) -> dict:
        entity_id = str(uuid.uuid4())
        entity = {"id": entity_id, **data}
        self._path(entity_id).write_text(json.dumps(entity, indent=2), encoding="utf-8")
        logger.debug("Created %s/%s", self._dir.name, entity_id)
        return entity

    def get(self, entity_id: str) -> Optional[dict]:
        path = self._path(entity_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[dict]:
        items = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(self._dir.glob("*.json"))
        ]
        logger.debug("Listed %d %s entities", len(items), self._dir.name)
        return items

    def update(self, entity_id: str, data: dict) -> Optional[dict]:
        path = self._path(entity_id)
        if not path.exists():
            return None
        entity = {"id": entity_id, **data}
        path.write_text(json.dumps(entity, indent=2), encoding="utf-8")
        logger.debug("Updated %s/%s", self._dir.name, entity_id)
        return entity

    def delete(self, entity_id: str) -> bool:
        path = self._path(entity_id)
        if not path.exists():
            return False
        path.unlink()
        logger.debug("Deleted %s/%s", self._dir.name, entity_id)
        return True
