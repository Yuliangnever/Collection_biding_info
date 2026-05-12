from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_yaml(relative_path: str) -> dict[str, Any]:
    path = PROJECT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for filename in (".env.example", ".env"):
        path = PROJECT_ROOT / filename
        if not path.exists():
            continue

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_settings() -> dict[str, Any]:
    settings = _load_yaml("config/settings.yaml")
    env_values = _load_env_values()

    if env_values.get("DATABASE_PATH"):
        settings["database_path"] = env_values["DATABASE_PATH"]
    if env_values.get("WEBHOOK_URL"):
        settings["webhook_url"] = env_values["WEBHOOK_URL"]
    if env_values.get("REQUEST_TIMEOUT"):
        settings["request_timeout"] = int(env_values["REQUEST_TIMEOUT"])

    settings["companies"] = _load_yaml("config/companies.yaml").get("companies", [])
    settings["keywords"] = _load_yaml("config/keywords.yaml").get("keywords", {})
    return settings
