from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_yaml(relative_path: str) -> dict[str, Any]:
    path = PROJECT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_settings() -> dict[str, Any]:
    settings = _load_yaml("config/settings.yaml")
    settings["companies"] = _load_yaml("config/companies.yaml").get("companies", [])
    settings["keywords"] = _load_yaml("config/keywords.yaml").get("keywords", {})
    return settings

