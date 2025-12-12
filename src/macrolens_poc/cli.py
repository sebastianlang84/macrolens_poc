from __future__ import annotations

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
from macrolens_poc.report.generate import (
    DEFAULT_DELTA_WINDOWS,
    generate_series_report,
    write_report_artifacts,
)
from macrolens_poc.sources import load_sources_matrix

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

    for spec in enabled:
        result = run_series(settings=settings, spec=spec, lookback_days=lookback_days)
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
        total_new_points += result.new_points

        logger.log(
            {
                "event": "series_run",
                "run_id": run_ctx.run_id,
                "series_id": result.series_id,
                "provider": result.provider,
                "status": result.status,
                "message": result.message,
                "stored_path": str(result.stored_path) if result.stored_path is not None else None,
                "new_points": result.new_points,
            }
        )

    summary = run_summary_event(ctx=run_ctx, status_counts=status_counts)
    summary["total_new_points"] = total_new_points
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

    logger.log(
        {
            "event": "series_run",
            "run_id": run_ctx.run_id,
            "series_id": result.series_id,
            "provider": result.provider,
            "status": result.status,
            "message": result.message,
            "stored_path": str(result.stored_path) if result.stored_path is not None else None,
            "new_points": result.new_points,
        }
    )

    status_counts = {"ok": 0, "warn": 0, "error": 0, "missing": 0}
    status_counts[result.status] = 1

    summary = run_summary_event(ctx=run_ctx, status_counts=status_counts)
    summary["total_new_points"] = result.new_points
    logger.log(summary)


@app.command()
def report(ctx: typer.Context) -> None:
    """Generate Markdown/JSON report from stored series."""

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
        }
    )

    matrix_result = load_sources_matrix(settings.sources_matrix_path)
    reports = []
    status_counts = {"ok": 0, "warn": 0, "error": 0, "missing": 0}

    for spec in matrix_result.matrix.series:
        series_report = generate_series_report(
            spec=spec,
            data_dir=settings.paths.data_dir,
            windows=DEFAULT_DELTA_WINDOWS,
        )
        status_counts[series_report.status] = status_counts.get(series_report.status, 0) + 1
        reports.append(series_report)

        logger.log(
            {
                "event": "series_report",
                "run_id": run_ctx.run_id,
                "series_id": series_report.series_id,
                "provider": series_report.provider,
                "status": series_report.status,
                "message": series_report.message,
                "last_date": series_report.last_date.isoformat() if series_report.last_date is not None else None,
                "last_value": series_report.last_value,
                "deltas": series_report.deltas,
                "path": str(series_report.path),
            }
        )

    artifacts = write_report_artifacts(
        reports=reports,
        reports_dir=settings.paths.reports_dir,
        report_tz=settings.report_tz,
        run_ctx=run_ctx,
        windows=DEFAULT_DELTA_WINDOWS,
    )

    logger.log(
        {
            "event": "report_written",
            "run_id": run_ctx.run_id,
            "markdown_path": str(artifacts["markdown"]),
            "json_path": str(artifacts["json"]),
            "series_total": len(reports),
        }
    )

    logger.log(run_summary_event(ctx=run_ctx, status_counts=status_counts))


if __name__ == "__main__":
    app()
