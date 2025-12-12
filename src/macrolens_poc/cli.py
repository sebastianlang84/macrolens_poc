from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from macrolens_poc.config import Settings, load_settings
from macrolens_poc.logging_utils import (
    JsonlLogger,
    default_log_path,
    new_run_context,
    run_summary_event,
)
from macrolens_poc.pipeline import run_series
from macrolens_poc.report import generate_report_v1
from macrolens_poc.sources import load_sources_matrix
from macrolens_poc.sources.matrix_status import (
    default_matrix_status_path,
    load_matrix_status,
    merge_matrix_status,
    save_matrix_status,
)

app = typer.Typer(add_completion=False, help="macrolens_poc CLI (Milestone M0 skeleton)")


def _ensure_dirs(settings: Settings) -> None:
    settings.paths.data_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.reports_dir.mkdir(parents=True, exist_ok=True)


@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        help="Path to YAML config (optional)",
    ),
) -> None:
    """Load settings and store them in Typer context."""

    settings = load_settings(config)
    _ensure_dirs(settings)
    ctx.obj = {"settings": settings}


@app.command("run-all")
def run_all(
    ctx: typer.Context,
    lookback_days: int = typer.Option(3650, "--lookback-days", help="How many days to backfill per series"),
) -> None:
    """Run ingestion for all enabled series."""

    settings: Settings = ctx.obj["settings"]
    run_ctx = new_run_context()
    logger = JsonlLogger(default_log_path(settings.paths.logs_dir, now_utc=run_ctx.started_at_utc))

    logger.log(
        {
            "event": "command_start",
            "command": "run-all",
            "run_id": run_ctx.run_id,
            "data_tz": settings.data_tz,
            "report_tz": settings.report_tz,
            "sources_matrix_path": str(settings.sources_matrix_path),
            "lookback_days": lookback_days,
        }
    )

    matrix_result = load_sources_matrix(settings.sources_matrix_path)
    enabled = [s for s in matrix_result.matrix.series if s.enabled]

    logger.log(
        {
            "event": "matrix_loaded",
            "run_id": run_ctx.run_id,
            "series_total": len(matrix_result.matrix.series),
            "series_enabled": len(enabled),
            "path": str(matrix_result.path),
        }
    )

    status_counts = {"ok": 0, "warn": 0, "error": 0, "missing": 0}
    total_new_points = 0
    results = []

    for spec in enabled:
        result = run_series(settings=settings, spec=spec, lookback_days=lookback_days)
        results.append(result)
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
        total_new_points += result.new_points

        event = {
            "event": "series_run",
            "run_id": run_ctx.run_id,
            "series_id": result.series_id,
            "provider": result.provider,
            "status": result.status,
            "message": result.message,
            "stored_path": str(result.stored_path) if result.stored_path is not None else None,
            "new_points": result.new_points,
            "revision_overwrites_count": getattr(result, "revision_overwrites_count", 0),
        }
        if getattr(result, "revision_overwrites_sample", None):
            event["revision_overwrites_sample"] = result.revision_overwrites_sample
        if getattr(result, "error_type", None):
            event["error_type"] = result.error_type
        if getattr(result, "error_message", None):
            event["error_message"] = result.error_message
        logger.log(event)

    matrix_status_entries_updated = 0
    matrix_status_persisted = False
    matrix_status_path = default_matrix_status_path(settings.paths.data_dir)
    try:
        existing_status = load_matrix_status(matrix_status_path)
        merge_result = merge_matrix_status(
            existing=existing_status,
            run_results=results,
            run_at_utc=datetime.now(timezone.utc),
        )
        save_matrix_status(matrix_status_path, merge_result.merged)
        matrix_status_entries_updated = merge_result.updated_entries
        matrix_status_persisted = True
        logger.log(
            {
                "event": "matrix_status_saved",
                "run_id": run_ctx.run_id,
                "path": str(matrix_status_path),
                "updated_entries": matrix_status_entries_updated,
            }
        )
    except Exception as exc:
        logger.log(
            {
                "event": "matrix_status_save_failed",
                "run_id": run_ctx.run_id,
                "path": str(matrix_status_path),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )

    summary = run_summary_event(ctx=run_ctx, status_counts=status_counts)
    summary["total_new_points"] = total_new_points
    summary["matrix_status_entries_updated"] = matrix_status_entries_updated
    summary["matrix_status_path"] = str(matrix_status_path)
    summary["matrix_status_persisted"] = matrix_status_persisted
    logger.log(summary)


@app.command("run-one")
def run_one(
    ctx: typer.Context,
    series_id: str = typer.Option(..., "--id", help="Internal series id"),
    lookback_days: int = typer.Option(3650, "--lookback-days", help="How many days to backfill"),
) -> None:
    """Run ingestion for a single series id."""

    settings: Settings = ctx.obj["settings"]
    run_ctx = new_run_context()
    logger = JsonlLogger(default_log_path(settings.paths.logs_dir, now_utc=run_ctx.started_at_utc))

    logger.log(
        {
            "event": "command_start",
            "command": "run-one",
            "run_id": run_ctx.run_id,
            "series_id": series_id,
            "data_tz": settings.data_tz,
            "report_tz": settings.report_tz,
            "sources_matrix_path": str(settings.sources_matrix_path),
            "lookback_days": lookback_days,
        }
    )

    matrix_result = load_sources_matrix(settings.sources_matrix_path)
    matches = [s for s in matrix_result.matrix.series if s.id == series_id]

    if not matches:
        logger.log(
            {
                "event": "series_not_found",
                "run_id": run_ctx.run_id,
                "series_id": series_id,
                "path": str(matrix_result.path),
            }
        )
        raise typer.Exit(code=2)

    spec = matches[0]
    if not spec.enabled:
        logger.log(
            {
                "event": "series_disabled",
                "run_id": run_ctx.run_id,
                "series_id": series_id,
            }
        )
        raise typer.Exit(code=3)

    logger.log(
        {
            "event": "series_selected",
            "run_id": run_ctx.run_id,
            "series_id": spec.id,
            "provider": spec.provider,
            "provider_symbol": spec.provider_symbol,
        }
    )

    result = run_series(settings=settings, spec=spec, lookback_days=lookback_days)

    event = {
        "event": "series_run",
        "run_id": run_ctx.run_id,
        "series_id": result.series_id,
        "provider": result.provider,
        "status": result.status,
        "message": result.message,
        "stored_path": str(result.stored_path) if result.stored_path is not None else None,
        "new_points": result.new_points,
        "revision_overwrites_count": getattr(result, "revision_overwrites_count", 0),
    }
    if getattr(result, "revision_overwrites_sample", None):
        event["revision_overwrites_sample"] = result.revision_overwrites_sample
    if getattr(result, "error_type", None):
        event["error_type"] = result.error_type
    if getattr(result, "error_message", None):
        event["error_message"] = result.error_message
    logger.log(event)

    matrix_status_entries_updated = 0
    matrix_status_persisted = False
    matrix_status_path = default_matrix_status_path(settings.paths.data_dir)
    try:
        existing_status = load_matrix_status(matrix_status_path)
        merge_result = merge_matrix_status(
            existing=existing_status,
            run_results=[result],
            run_at_utc=datetime.now(timezone.utc),
        )
        save_matrix_status(matrix_status_path, merge_result.merged)
        matrix_status_entries_updated = merge_result.updated_entries
        matrix_status_persisted = True
        logger.log(
            {
                "event": "matrix_status_saved",
                "run_id": run_ctx.run_id,
                "path": str(matrix_status_path),
                "updated_entries": matrix_status_entries_updated,
            }
        )
    except Exception as exc:
        logger.log(
            {
                "event": "matrix_status_save_failed",
                "run_id": run_ctx.run_id,
                "path": str(matrix_status_path),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )

    status_counts = {"ok": 0, "warn": 0, "error": 0, "missing": 0}
    status_counts[result.status] = 1

    summary = run_summary_event(ctx=run_ctx, status_counts=status_counts)
    summary["total_new_points"] = result.new_points
    summary["matrix_status_entries_updated"] = matrix_status_entries_updated
    summary["matrix_status_path"] = str(matrix_status_path)
    summary["matrix_status_persisted"] = matrix_status_persisted
    logger.log(summary)


@app.command()
def report(ctx: typer.Context) -> None:
    """Generate Report v1 (Markdown + JSON) from stored series."""

    settings: Settings = ctx.obj["settings"]
    run_ctx = new_run_context()
    logger = JsonlLogger(default_log_path(settings.paths.logs_dir, now_utc=run_ctx.started_at_utc))

    logger.log(
        {
            "event": "command_start",
            "command": "report",
            "run_id": run_ctx.run_id,
            "data_tz": settings.data_tz,
            "report_tz": settings.report_tz,
            "sources_matrix_path": str(settings.sources_matrix_path),
        }
    )

    result = generate_report_v1(settings=settings, now_utc=datetime.now(timezone.utc))

    logger.log(
        {
            "event": "report_generated",
            "run_id": run_ctx.run_id,
            "as_of_date": result.report.meta.get("as_of_date"),
            "md_path": str(result.md_path),
            "json_path": str(result.json_path),
            "series_count": len(result.report.table),
            "risk_flags": result.report.risk_flags,
        }
    )

    logger.log(run_summary_event(ctx=run_ctx, status_counts={"ok": 1, "warn": 0, "error": 0, "missing": 0}))


if __name__ == "__main__":
    app()
