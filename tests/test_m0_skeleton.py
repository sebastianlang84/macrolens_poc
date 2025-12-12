from __future__ import annotations

from pathlib import Path

import pytest

from macrolens_poc.config import load_settings


def test_config_loads_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure env does not affect defaults
    monkeypatch.delenv("DATA_TZ", raising=False)
    monkeypatch.delenv("REPORT_TZ", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    settings = load_settings(config_path=None)
    assert settings.data_tz == "UTC"
    assert settings.report_tz == "Europe/Vienna"
    assert settings.fred_api_key is None


def test_config_loads_yaml_overrides(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "data_tz: 'UTC'\nreport_tz: 'Europe/Vienna'\nsources_matrix_path: 'config/sources_matrix.yaml'\npaths:\n  data_dir: 'data'\n  logs_dir: 'logs'\n  reports_dir: 'reports'\n",
        encoding="utf-8",
    )

    settings = load_settings(config_path=cfg)
    assert settings.data_tz == "UTC"
    assert settings.report_tz == "Europe/Vienna"
    assert settings.sources_matrix_path.as_posix().endswith("config/sources_matrix.yaml")
    assert settings.paths.data_dir.name == "data"


def test_cli_importable() -> None:
    import macrolens_poc.cli  # noqa: F401
