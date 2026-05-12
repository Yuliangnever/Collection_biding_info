from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

try:
    from src.embedded_config import BUILTIN_WEBHOOK_URL
except ImportError:
    BUILTIN_WEBHOOK_URL = ""


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _root_candidates() -> list[Path]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent)
        bundle_path = getattr(sys, "_MEIPASS", None)
        if bundle_path:
            candidates.append(Path(bundle_path).resolve())
    candidates.extend([Path.cwd().resolve(), PROJECT_ROOT])

    unique_candidates: list[Path] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def _find_existing_path(relative_path: str) -> Path:
    for root in _root_candidates():
        path = root / relative_path
        if path.exists():
            return path
    return PROJECT_ROOT / relative_path


def _load_yaml(relative_path: str) -> dict[str, Any]:
    path = _find_existing_path(relative_path)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for root in reversed(_root_candidates()):
        for filename in (".env.example", ".env"):
            path = root / filename
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

    if BUILTIN_WEBHOOK_URL:
        settings["webhook_url"] = BUILTIN_WEBHOOK_URL
    if env_values.get("DATABASE_PATH"):
        settings["database_path"] = env_values["DATABASE_PATH"]
    if env_values.get("WEBHOOK_URL"):
        settings["webhook_url"] = env_values["WEBHOOK_URL"]
    if env_values.get("REQUEST_TIMEOUT"):
        settings["request_timeout"] = int(env_values["REQUEST_TIMEOUT"])

    database_path = Path(str(settings.get("database_path", "data/tenders.sqlite3")))
    if not database_path.is_absolute():
        settings["database_path"] = str(_root_candidates()[0] / database_path)

    settings["companies"] = _load_yaml("config/companies.yaml").get("companies", [])
    settings["keywords"] = _load_yaml("config/keywords.yaml").get("keywords", {})
    settings["sources"] = _load_yaml("config/sources.yaml").get("sources", [])
    return settings
