# apps/api/main.py
"""FastAPI application root re-export for Kautilya AI."""

try:
    from src.main import app
except ImportError:
    from apps.src.main import app

__all__ = ["app"]
