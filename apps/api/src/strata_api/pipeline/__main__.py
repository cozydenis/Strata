"""CLI entry point: python -m strata_api.pipeline [stadt|kanton|both]

Usage:
    python -m strata_api.pipeline stadt          # run Stadt Zürich pipeline
    python -m strata_api.pipeline kanton         # run Kanton Zürich pipeline
    python -m strata_api.pipeline both           # run stadt then kanton
    DATABASE_URL=sqlite:///./local.db python -m strata_api.pipeline stadt
"""
from __future__ import annotations

import sys


def main(args: list[str] | None = None) -> int:
    if args is None:
        args = sys.argv[1:]

    if not args or args[0] not in {"stadt", "kanton", "both"}:
        print("Usage: python -m strata_api.pipeline [stadt|kanton|both]", file=sys.stderr)
        return 1

    from strata_api.db.base import Base
    from strata_api.db.session import get_engine
    from strata_api.pipeline.runner import run_kanton_pipeline, run_stadt_pipeline

    engine = get_engine()
    Base.metadata.create_all(engine)  # no-op if tables already exist

    sources = ["stadt", "kanton"] if args[0] == "both" else [args[0]]

    for source in sources:
        print(f"[pipeline] starting {source} run…")
        if source == "stadt":
            result = run_stadt_pipeline(engine)
        else:
            result = run_kanton_pipeline(engine)

        if result.status == "completed":
            print(
                f"[pipeline] {source} done — "
                f"buildings={result.buildings_upserted}, "
                f"entrances={result.entrances_upserted}, "
                f"units={result.units_upserted}"
            )
        else:
            print(f"[pipeline] {source} FAILED — {result.error_message}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
