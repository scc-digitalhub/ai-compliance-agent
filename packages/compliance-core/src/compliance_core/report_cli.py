"""External CLI/runtime for deterministic report preview and publication.

This module consumes canonical result JSON and known evaluator outputs. It never loads or executes
arbitrary Python source. Publishing uses one report-repository batch operation after all reports
have been built, normalized, validated, and preflighted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .reporting import build_reports, validate_report
from .report_tools import prepare_report
from .specification_tools import specification_revision
from .state import InMemoryStateStore

MAX_RESULTS_BYTES = 10 * 1024 * 1024
DEFAULT_REPORT_NAMES = {"EVALUATION": "compliance-evaluation", "TEST": "compliance-test"}


class ReportCliError(ValueError):
    """Expected user-facing CLI validation or publication failure."""


def _read_results(source: str, stdin: Any = None) -> list[dict[str, Any]]:
    if source == "-":
        stream = stdin if stdin is not None else sys.stdin
        raw = stream.read(MAX_RESULTS_BYTES + 1)
        if isinstance(raw, str):
            payload = raw.encode("utf-8")
        else:
            payload = raw
    else:
        path = Path(source).expanduser()
        try:
            with path.open("rb") as handle:
                payload = handle.read(MAX_RESULTS_BYTES + 1)
        except OSError as exc:
            raise ReportCliError(f"Could not read result input: {exc}") from exc
    if len(payload) > MAX_RESULTS_BYTES:
        raise ReportCliError(f"Result input exceeds {MAX_RESULTS_BYTES} bytes.")
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReportCliError(f"Result input must be canonical UTF-8 JSON: {exc}") from exc
    results = decoded.get("results") if isinstance(decoded, dict) else decoded
    if not isinstance(results, list) or not results:
        raise ReportCliError("Result input must be a non-empty array or an object with a results array.")
    if any(not isinstance(item, dict) for item in results):
        raise ReportCliError("Each result must be a JSON object.")
    return results


def _report_names(names: dict[str, str] | None, variants: Sequence[str]) -> dict[str, str]:
    requested = names or {}
    unknown = set(requested) - set(variants)
    if unknown:
        raise ReportCliError(f"Report names supplied for unrequested variants: {sorted(unknown)}")
    resolved = {variant: requested.get(variant, DEFAULT_REPORT_NAMES[variant]) for variant in variants}
    if any(not name.strip() for name in resolved.values()) or len(set(resolved.values())) != len(resolved):
        raise ReportCliError("Report names must be non-empty and unique.")
    return resolved


def run_report_workflow(
    results: Any,
    *,
    mode: str,
    project: str,
    entity_kind: str,
    entity: str,
    entity_version: str | None = None,
    variants: Sequence[str] = ("EVALUATION",),
    lineage: dict[str, Any] | None = None,
    names: dict[str, str] | None = None,
    repository: Any = None,
    overwrite: bool = False,
    strict_atomic: bool = False,
) -> dict[str, Any]:
    """Build/validate reports and optionally stage them through one repository batch write.

    The repository can be injected by trusted external runtimes/tests. Preview never calls it.
    """
    if mode not in {"preview", "publish"}:
        raise ReportCliError("mode must be 'preview' or 'publish'.")
    if not project.strip() or not entity.strip():
        raise ReportCliError("An explicit project and entity are required.")
    if entity_kind not in {"dataset", "model"}:
        raise ReportCliError("entity_kind must be 'dataset' or 'model'.")
    if strict_atomic and mode == "publish":
        if repository is None:
            repository = _load_default_repository()
        if not getattr(repository, "supports_atomic_batch", False):
            raise ReportCliError("Strict atomic publication is not supported by this report repository.")

    built = build_reports(results, variants=variants, lineage=lineage)
    target = built["target"]
    if target["project"] != project or target["entity"] != entity:
        raise ReportCliError("Result target does not exactly match the explicitly requested project/entity.")
    if entity_version is not None and target["entity_version"] != entity_version:
        raise ReportCliError("Result entity_version does not match the explicitly requested target version.")
    if set(built["reports"]) != set(variants):
        raise ReportCliError(
            "The complete requested report set could not be built: "
            + "; ".join(issue["message"] for issue in built["issues"])
        )
    report_names = _report_names(names, variants)
    state = InMemoryStateStore()
    prepared = {}
    for kind in variants:
        normalized = validate_report(built["reports"][kind]).model_dump(
            mode="json", exclude_none=True, by_alias=True,
        )
        item = prepare_report(state, entity_kind, entity, report_names[kind], normalized, project)
        prepared[kind] = item["report"]

    expected_revision = target["specification_revision"]
    result: dict[str, Any] = {
        "status": "preview" if mode == "preview" else "staged",
        "target": {
            "project": project,
            "entity_kind": entity_kind,
            "entity": entity,
            "entity_version": target["entity_version"],
        },
        "reports": [
            {"kind": kind, "name": report_names[kind], "report": prepared[kind]}
            for kind in variants
        ],
        "issues": built["issues"],
        "objective_references": built["objective_references"],
        "provenance": built["provenance"],
        "publication": {
            "requested": mode == "publish",
            "write_performed": False,
            "strict_atomic": strict_atomic,
            "atomicity": "not applicable; preview mode performs no writes" if mode == "preview"
            else "pending; adapter guarantee must be reported",
        },
        "revision_check": {
            "status": "not_available",
            "expected_revision": expected_revision,
            "current_revision": None,
            "reason": "The report repository does not expose a live specification revision reader.",
        },
    }
    if mode == "preview":
        return result

    if repository is None:
        repository = _load_default_repository()
    revision_check = result["revision_check"]
    if expected_revision is None:
        revision_check["reason"] = "The supplied measurement has no specification_revision to compare."
    elif callable(revision_reader := getattr(repository, "get_specification_revision", None)):
        try:
            current_revision = revision_reader(entity_kind, entity, project=project)
        except Exception as exc:
            raise ReportCliError(
                f"Could not verify the current compliance specification ({type(exc).__name__})."
            ) from exc
        if expected_revision is not None and current_revision is None:
            raise ReportCliError(
                "The result names a specification revision, but no current target specification could be read."
            )
        if expected_revision is not None and current_revision != expected_revision:
            raise ReportCliError(
                "The compliance specification changed after evaluation; regenerate against the current snapshot."
            )
        revision_check.update({
            "status": "matched",
            "current_revision": current_revision,
            "reason": "Matched at pre-publication check; the repository provides no compare-and-swap guarantee.",
        })
    else:
        revision_check["reason"] = (
            "The supplied result revision was not checked against the live target; "
            "this repository has no get_specification_revision method."
        )
    existing = {}
    for kind, name in report_names.items():
        try:
            current = repository.get(entity_kind, entity, name, project=project)
        except Exception as exc:
            raise ReportCliError(
                f"Could not preflight report '{name}' ({type(exc).__name__})."
            ) from exc
        if current:
            existing[kind] = specification_revision(current)
    if existing and not overwrite:
        raise ReportCliError(
            "Named report(s) already exist; pass --overwrite only after reviewing their replacement: "
            + ", ".join(report_names[kind] for kind in existing)
        )
    report_batch = {report_names[kind]: prepared[kind] for kind in variants}
    try:
        save_batch = getattr(repository, "save_batch", None)
        if save_batch is not None:
            save_batch(entity_kind, entity, report_batch, project=project, strict_atomic=strict_atomic)
        elif len(report_batch) == 1:
            name, report = next(iter(report_batch.items()))
            repository.save(entity_kind, entity, name, report, project=project)
        else:
            raise ReportCliError("Repository cannot publish a multi-report set with one batch operation.")
    except ReportCliError:
        raise
    except Exception as exc:
        raise ReportCliError(f"Report publication failed ({type(exc).__name__}).") from exc

    receipts = []
    for kind, name in report_names.items():
        try:
            stored = repository.get(entity_kind, entity, name, project=project)
        except Exception:
            stored = None
        receipts.append({
            "kind": kind,
            "name": name,
            "extension_kind": "compliance-report",
            "saved": True,
            "revision": specification_revision(stored) if stored else None,
        })
    result["status"] = "published"
    result["receipts"] = receipts
    result["publication"] = {
        "requested": True,
        "write_performed": True,
        "strict_atomic": strict_atomic,
        "atomicity": (
            "repository reports atomic batch support"
            if getattr(repository, "supports_atomic_batch", False)
            else "one repository batch call; transaction/concurrency atomicity is not guaranteed"
        ),
    }
    return result


def _load_default_repository() -> Any:
    try:
        from compliance_dh.repositories import DhReportRepository
    except ImportError as exc:
        raise ReportCliError(
            "Publishing requires the DigitalHub integration extra and an authenticated external runtime."
        ) from exc
    return DhReportRepository()


def _parse_name_options(values: Sequence[str]) -> dict[str, str]:
    parsed = {}
    for value in values:
        kind, separator, name = value.partition("=")
        if not separator or kind not in {"EVALUATION", "TEST"} or not name.strip():
            raise ReportCliError("--report-name must be KIND=NAME for EVALUATION or TEST.")
        if kind in parsed:
            raise ReportCliError(f"Duplicate --report-name for {kind}.")
        parsed[kind] = name
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="compliance-report")
    subparsers = parser.add_subparsers(dest="mode", required=True)
    for mode in ("preview", "publish"):
        command = subparsers.add_parser(mode, help=f"{mode.capitalize()} validated reports")
        command.add_argument("--results", required=True, help="Canonical JSON path, or '-' for stdin")
        command.add_argument("--project", required=True)
        command.add_argument("--entity-kind", required=True, choices=("dataset", "model"))
        command.add_argument("--entity", required=True)
        command.add_argument("--entity-version")
        command.add_argument("--variants", default="EVALUATION",
                             help="Comma-separated EVALUATION and/or TEST variants")
        command.add_argument("--lineage-json", help="Optional JSON object for report lineage")
        command.add_argument("--report-name", action="append", default=[], metavar="KIND=NAME")
        if mode == "publish":
            command.add_argument("--overwrite", action="store_true")
            command.add_argument("--strict-atomic", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None, *, repository: Any = None, stdin: Any = None) -> int:
    """CLI entry point. Returns 0 on successful preview/publication, 2 on failure."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        variants = [item.strip() for item in args.variants.split(",") if item.strip()]
        if not variants or any(item not in {"EVALUATION", "TEST"} for item in variants):
            raise ReportCliError("--variants must contain EVALUATION and/or TEST.")
        raw_results = _read_results(args.results, stdin=stdin)
        lineage = json.loads(args.lineage_json) if args.lineage_json else None
        if lineage is not None and not isinstance(lineage, dict):
            raise ReportCliError("--lineage-json must decode to an object.")
        output = run_report_workflow(
            raw_results, mode=args.mode, project=args.project, entity_kind=args.entity_kind,
            entity=args.entity, entity_version=args.entity_version, variants=variants, lineage=lineage,
            names=_parse_name_options(args.report_name), repository=repository,
            overwrite=getattr(args, "overwrite", False),
            strict_atomic=getattr(args, "strict_atomic", False),
        )
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, allow_nan=False))
        return 0
    except (ReportCliError, ValueError, TypeError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            json.dumps({"status": "error", "error": f"Unexpected failure ({type(exc).__name__})."}),
            file=sys.stderr,
        )
        return 2


__all__ = ["MAX_RESULTS_BYTES", "ReportCliError", "build_parser", "main", "run_report_workflow"]


if __name__ == "__main__":  # pragma: no cover - exercised by the installed console script
    raise SystemExit(main())
