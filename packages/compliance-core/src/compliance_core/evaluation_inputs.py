# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Bounded canonical JSON evidence loading via local files or authorized readers.

No URL fetching, code execution, or filename-derived metric/objective inference.
Noncanonical JSON requires an explicit destination-field to source-pointer mapping.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from .contracts.metric_evaluation import MeasurementEnvelope
from .metric_evaluation import select_value

MAX_INPUT_BYTES = 2 * 1024 * 1024


class InputError(ValueError):
    def __init__(self, message: str, code: str = "invalid_input"):
        super().__init__(message)
        self.code = code


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise InputError(f"duplicate JSON key '{key}'")
        value[key] = item
    return value


def _read_local(source: str, allowed_root: str | Path | None, max_bytes: int) -> bytes:
    parsed = urlparse(source)
    if parsed.scheme and parsed.scheme != "file":
        raise InputError("Reference requires an injected authorized reader", "unsupported_reference")
    if parsed.scheme == "file" and parsed.netloc not in ("", "localhost"):
        raise InputError("Remote file authorities are not supported", "unauthorized_path")
    raw = unquote(parsed.path) if parsed.scheme == "file" else source
    root = Path(allowed_root or Path.cwd()).resolve()
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise InputError("Input file is outside the authorized root", "unauthorized_path")
        # Refuse symlinks, including symlinked parent components, rather than
        # relying only on a resolve-before-open authorization check.
        relative = path.absolute().relative_to(root)
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for component in relative.parts[:-1]:
                next_directory = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory)
                directory = next_directory
            descriptor = os.open(relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            with os.fdopen(descriptor, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise InputError("Evidence source must be a regular file", "unauthorized_path")
                if info.st_size > max_bytes:
                    raise InputError("Evidence source exceeds the size limit", "input_too_large")
                data = stream.read(max_bytes + 1)
        finally:
            os.close(directory)
    except InputError:
        raise
    except (OSError, ValueError, IndexError) as exc:
        raise InputError(f"Cannot access evidence file: {exc}", "input_unavailable") from exc
    return data


def load_results(
    source: str, *, allowed_root: str | Path | None = None,
    reader: Callable[[str], bytes] | None = None, max_bytes: int = MAX_INPUT_BYTES,
    format: str = "json", mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    if format != "json":
        raise InputError("Only canonical JSON or explicitly mapped JSON is supported", "unsupported_format")
    if not isinstance(source, str) or not source or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise InputError("A source identity and a positive size limit are required")
    try:
        raw = reader(source) if reader is not None else _read_local(source, allowed_root, max_bytes)
    except InputError:
        raise
    except Exception as exc:
        raise InputError(f"Authorized reader could not resolve source: {exc}", "input_unavailable") from exc
    if not isinstance(raw, bytes):
        raise InputError("Authorized readers must return immutable bytes")
    if len(raw) > max_bytes:
        raise InputError("Evidence source exceeds the size limit", "input_too_large")
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                            parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"Nonfinite JSON value {value}")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError(f"Malformed JSON evidence: {exc}") from exc
    records = parsed.get("results") if isinstance(parsed, dict) and "results" in parsed else parsed
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list) or not records:
        raise InputError("JSON evidence must contain a nonempty result list")
    if mapping is not None:
        if not isinstance(mapping, dict) or not mapping or not all(isinstance(v, str) for v in mapping.values()):
            raise InputError("Mapping must explicitly map envelope fields to source JSON pointers")
        if set(mapping) - set(MeasurementEnvelope.model_fields):
            raise InputError("Mapping contains unknown destination fields")
        try:
            records = [{field: select_value(record, pointer) for field, pointer in mapping.items()} for record in records]
        except ValueError as exc:
            raise InputError(str(exc)) from exc
    identity = {"identity": source, "sha256": hashlib.sha256(raw).hexdigest(),
                "format": format, "mapping": mapping, "size_bytes": len(raw)}
    try:
        results = []
        for record in records:
            result = MeasurementEnvelope.model_validate(record).model_dump(mode="json", exclude_none=True)
            result["provenance"] = {**result.get("provenance", {}), "external_source": identity,
                                    "verification": "externally_supplied_not_independently_verified"}
            results.append(result)
    except ValueError as exc:
        raise InputError(f"Invalid measurement envelope: {exc}") from exc
    return {"results": results, "source": identity}
