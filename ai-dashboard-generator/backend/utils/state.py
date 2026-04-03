from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import pandas as pd


@dataclass
class AppState:
    datasets: Dict[str, pd.DataFrame] = field(default_factory=dict)
    schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_dashboard: Dict[str, Any] = field(default_factory=lambda: {"charts": [], "insights": [], "layout": {}})


STATE = AppState()


def set_dataset(name: str, df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    STATE.datasets[name] = df
    STATE.schemas[name] = schema


def dataset_names() -> List[str]:
    return list(STATE.datasets.keys())

