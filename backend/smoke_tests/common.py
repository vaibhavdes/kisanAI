import importlib
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise RuntimeError("Install python-dotenv first: pip install -r requirements.txt") from exc


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} missing. Add it to local .env, not .env.example.")
    return value


def optional_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name) or default


def require_package(module_name: str, install_hint: str) -> None:
    try:
        importlib.import_module(module_name)
    except ImportError as exc:
        raise RuntimeError(f"Missing package {module_name}. Install with: {install_hint}") from exc


def print_ok(message: str) -> None:
    print(f"OK: {message}")
