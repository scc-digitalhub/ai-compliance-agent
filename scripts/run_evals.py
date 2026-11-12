# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

"""Run the compliance benchmark against one or more models and write a comparison report.

Example:
    uv run --extra api python scripts/run_evals.py --model openai/gpt-4.1 --model gemini/gemini-2.5-pro \
        --out eval-report.json --markdown eval-report.md

Requires provider credentials for each model (LiteLLM conventions, or LLM_API_BASE/LLM_API_KEY for
a gateway). DigitalHub tools are disabled unless --with-dh is given.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


async def run(args: argparse.Namespace) -> int:
    from compliance_api.config import ApiSettings
    from compliance_api.engine import create_delegated_engine
    from compliance_core.evaluation import evaluate, load_cases, render_markdown
    from compliance_core.knowledge import get_bundle

    cases = load_cases(args.cases)
    if args.case:
        cases = [case for case in cases if case.id in set(args.case)]
    bundle = get_bundle()
    reports = []
    for model in args.model:
        settings = ApiSettings(
            structured_model=model, max_validation_retries=args.retries, request_timeout_s=args.timeout,
            enable_dh=args.with_dh,
        )
        report = await evaluate(
            cases, create_delegated_engine(settings), bundle, label=model, concurrency=args.concurrency,
        )
        reports.append(report)
        print(f"{model}: {json.dumps(report.summary)}", file=sys.stderr)

    if args.out:
        args.out.write_text(json.dumps([report.model_dump(mode="json") for report in reports], indent=2) + "\n")
    markdown = render_markdown(reports)
    if args.markdown:
        args.markdown.write_text(markdown)
    else:
        print(markdown)
    if args.min_validity is not None:
        failing = [r.label for r in reports if (r.summary["validity_rate"] or 0) < args.min_validity]
        if failing:
            print(f"Validity below {args.min_validity}: {', '.join(failing)}", file=sys.stderr)
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", action="append", required=True, help="LiteLLM model id; repeat to compare")
    parser.add_argument("--cases", type=Path, default=ROOT / "evals" / "cases.json")
    parser.add_argument("--case", action="append", help="Run only the case with this id; repeatable")
    parser.add_argument("--retries", type=int, default=2, help="Validation retries per case")
    parser.add_argument("--timeout", type=float, default=300.0, help="Seconds per case")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--out", type=Path, help="Write the full JSON report here")
    parser.add_argument("--markdown", type=Path, help="Write the Markdown comparison here instead of stdout")
    parser.add_argument("--min-validity", type=float, help="Exit with an error below this validity rate")
    parser.add_argument(
        "--with-dh", action="store_true",
        help="Let analyses consult DigitalHub; off by default so results do not depend on stored specifications",
    )
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
