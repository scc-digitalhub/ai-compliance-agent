"""Read-only, cached access to the Open Knowledge Format (OKF) bundle."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ..config import get_settings

logger = logging.getLogger(__name__)

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
_INSTANCE = re.compile(r"#\s*Instance\s*\n+```json\s*\n(.*?)```", re.DOTALL)
_APPLIES_TO = re.compile(r"\*\*Applies to\*\*:\s*([^|\n]+)")
_TOP_LEVEL_KEY = re.compile(r"^(\w+):\s*(.*)$")
_SKIP_NAMES = {"index.md", "log.md"}


@dataclass(frozen=True)
class Concept:
    path: str  # bundle-relative, posix
    type: str
    title: str
    description: str
    tags: tuple[str, ...]
    instance: dict[str, Any] | None
    applies_to: str
    text_lower: str = field(repr=False, compare=False)

    @property
    def id(self) -> str | None:
        return (self.instance or {}).get("id")

    def record(self, with_instance: bool = True) -> dict[str, Any]:
        rec: dict[str, Any] = {
            "path": self.path,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
        }
        if with_instance and self.instance is not None:
            rec["instance"] = self.instance
        return rec


def _parse_instance(text: str) -> dict[str, Any] | None:
    m = _INSTANCE.search(text)
    if not m:
        return None
    raw = m.group(1)
    for candidate in (raw, raw.replace("{{", "{").replace("}}", "}")):  # some catalog files are templated
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return value if isinstance(value, dict) else None
    return None


def _lenient_frontmatter(block: str) -> dict[str, Any]:
    """Line-based fallback for front-matter that is not valid YAML (e.g. unquoted ': ' in values)."""
    meta: dict[str, Any] = {}
    for line in block.splitlines():
        m = _TOP_LEVEL_KEY.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if key == "tags" and value.startswith("["):
            meta[key] = [t.strip().strip("'\"") for t in value.strip("[]").split(",") if t.strip()]
        else:
            meta[key] = value.strip("'\"")
    return meta


def _parse_concept(rel: str, text: str) -> Concept:
    meta: dict[str, Any] = {}
    m = _FRONTMATTER.match(text)
    if m:
        try:
            loaded = yaml.safe_load(m.group(1))
            meta = loaded if isinstance(loaded, dict) else {}
        except yaml.YAMLError:
            meta = _lenient_frontmatter(m.group(1))
    applies = _APPLIES_TO.search(text)
    return Concept(
        path=rel,
        type=str(meta.get("type", "")),
        title=str(meta.get("title", Path(rel).stem)),
        description=" ".join(str(meta.get("description", "")).split()),
        tags=tuple(str(t) for t in (meta.get("tags") or [])),
        instance=_parse_instance(text),
        applies_to=applies.group(1).strip() if applies else "",
        text_lower=text.lower(),
    )


class OkfBundle:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"OKF bundle not found: {self.root}")
        digest = hashlib.sha256()
        concepts: dict[str, Concept] = {}
        for md in sorted(self.root.rglob("*.md")):
            rel = md.relative_to(self.root).as_posix()
            text = md.read_text(encoding="utf-8")
            digest.update(rel.encode())
            digest.update(text.encode())
            if md.name not in _SKIP_NAMES:
                concepts[rel] = _parse_concept(rel, text)
        self.concepts = concepts
        self.version = digest.hexdigest()[:12]

    # -- path handling --------------------------------------------------------

    def resolve(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if not p.is_relative_to(self.root):
            raise ValueError(f"Path outside the OKF bundle: {rel}")
        return p

    # -- navigation -----------------------------------------------------------

    def list_directory(self, rel: str) -> str:
        d = self.resolve(rel)
        index = d / "index.md"
        if index.is_file():
            return index.read_text(encoding="utf-8")
        if d.is_dir():
            names = sorted(f.name for f in d.iterdir() if f.suffix == ".md")
            return f"Contents of {rel}:\n" + "\n".join(names)
        return f"[Directory not found: {rel}]"

    def read(self, rel: str) -> str:
        p = self.resolve(rel)
        if p.suffix != ".md" or not p.is_file():
            return f"[NOT FOUND: {rel}]"
        return p.read_text(encoding="utf-8")

    # -- queries --------------------------------------------------------------

    def under(self, subdir: str, keyword: str = "") -> list[Concept]:
        prefix = subdir.strip("/") + "/"
        kw = keyword.lower()
        return [
            c for p, c in self.concepts.items() if p.startswith(prefix) and (not kw or kw in c.text_lower)
        ]

    def subdirectories(self, subdir: str) -> list[str]:
        d = self.resolve(subdir)
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.is_dir() else []

    def search(self, query: str, category: str = "", limit: int = 25) -> tuple[int, list[Concept]]:
        words = [w.lower() for w in query.split() if w]
        prefix = (category.strip("/") or "catalog") + "/"
        scored = []
        for path, concept in self.concepts.items():
            if not path.startswith(prefix):
                continue
            score = sum(1 for w in words if w in concept.text_lower)
            if score:
                scored.append((score, path, concept))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return len(scored), [c for _, _, c in scored[:limit]]

    def ids_of_type(self, type_: str) -> set[str]:
        return {c.id for c in self.concepts.values() if c.type == type_ and c.id}


@lru_cache
def get_bundle() -> OkfBundle:
    return OkfBundle(get_settings().okf_path)
