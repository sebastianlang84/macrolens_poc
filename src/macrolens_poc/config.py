from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class PathsConfig(BaseModel):
    data_dir: Path = Field(default=Path("data"))
    logs_dir: Path = Field(default=Path("logs"))
    reports_dir: Path = Field(default=Path("reports"))
    metadata_db: Path = Field(default=Path("data/metadata.sqlite"))


class Settings(BaseModel):
    """Application settings.

    TZ conventions:
    - data_tz is canonical for stored timestamps (default UTC)
    - report_tz is presentation timezone for reports (default Europe/Vienna)

    Sources matrix:
    - sources_matrix_path points to the YAML that lists all series (single source of truth).

    Provider keys:
    - fred_api_key is read from env/YAML and must not be committed.
    """

    data_tz: str = Field(default="UTC")
    report_tz: str = Field(default="Europe/Vienna")

    sources_matrix_path: Path = Field(default=Path("config/sources_matrix.yaml"))

    fred_api_key: Optional[str] = Field(default=None)

    paths: PathsConfig = Field(default_factory=PathsConfig)


def load_settings(config_path: Optional[Path]) -> Settings:
    """Load settings from .env + optional YAML.

    Precedence:
      1) defaults
      2) .env (DATA_TZ / REPORT_TZ)
      3) YAML file (if provided)

    Notes:
      - This function only validates presence/types, not timezone existence.
        Timezone validation will be added when we introduce timezone-aware
        conversions in later milestones.
    """

    load_dotenv(override=False)

    # start from defaults via pydantic
    base = Settings()

    # P0: defaults
    merged: Dict[str, Any] = base.model_dump(mode="python")

    # P1: .env overrides (canonical names in env are upper-case)
    env_data_tz = _getenv("DATA_TZ")
    env_report_tz = _getenv("REPORT_TZ")
    env_fred_api_key = _getenv("FRED_API_KEY")

    if env_data_tz is not None:
        merged["data_tz"] = env_data_tz
    if env_report_tz is not None:
        merged["report_tz"] = env_report_tz
    if env_fred_api_key is not None:
        merged["fred_api_key"] = env_fred_api_key

    if config_path is not None:
        cfg = _load_yaml(config_path)
        merged = _deep_merge(merged, cfg)

    try:
        # pydantic converts to Path types
        return Settings.model_validate(merged)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration: {exc}") from exc


def _getenv(key: str) -> Optional[str]:
    import os

    value = os.getenv(key)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    raw = path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw) or {}
    if not isinstance(parsed, dict):
        raise ValueError("YAML config must be a mapping/object at the top level")
    return parsed


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if (
            k in out
            and isinstance(out[k], dict)
            and isinstance(v, dict)
        ):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
