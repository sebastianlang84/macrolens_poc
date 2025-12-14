from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


Provider = Literal["fred", "yfinance"]


class SeriesSpec(BaseModel):
    id: str
    provider: Provider
    provider_symbol: str

    category: str
    frequency_target: str = Field(default="daily")
    timezone: str = Field(default="UTC")
    units: str = Field(default="")
    transform: str = Field(default="none")
    notes: str = Field(default="")

    # Staleness override (if None, use global default)
    stale_days: Optional[int] = Field(default=None)

    enabled: bool = Field(default=True)

    # system-maintained (optional in static matrix file)
    last_ok: Optional[str] = Field(default=None)
    status: Optional[Literal["ok", "warn", "error", "missing"]] = Field(default=None)


class SourcesMatrix(BaseModel):
    version: int = Field(default=1)
    series: List[SeriesSpec]


@dataclass(frozen=True)
class MatrixLoadResult:
    matrix: SourcesMatrix
    path: Path


def load_sources_matrix(path: Path) -> MatrixLoadResult:
    """Load and validate the data-source-matrix.

    The matrix is a YAML mapping with keys:
      - version: int
      - series: list[SeriesSpec]

    System-maintained fields (last_ok/status) are optional.
    """

    if not path.exists():
        raise FileNotFoundError(str(path))

    raw = path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw) or {}
    if not isinstance(parsed, dict):
        raise ValueError("sources matrix must be a mapping/object at the top level")

    try:
        matrix = SourcesMatrix.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"Invalid sources matrix: {exc}") from exc

    _validate_uniqueness(matrix)

    # Ensure deterministic order by sorting series by ID
    matrix.series.sort(key=lambda s: s.id)

    return MatrixLoadResult(matrix=matrix, path=path)


def _validate_uniqueness(matrix: SourcesMatrix) -> None:
    ids = [s.id for s in matrix.series]
    dup_ids = _find_dupes(ids)
    if dup_ids:
        raise ValueError(f"Duplicate series ids in sources matrix: {sorted(dup_ids)}")


def _find_dupes(values: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    dup: List[str] = []
    for v in values:
        seen[v] = seen.get(v, 0) + 1
        if seen[v] == 2:
            dup.append(v)
    return dup
