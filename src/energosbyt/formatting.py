from datetime import date, datetime
from typing import Any


def format_row(row: dict[str, Any]) -> dict[str, Any]:
    """Render ClickHouse date values in the format required by the lab API."""
    formatted = {}
    for name, value in row.items():
        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, date):
            value = value.isoformat()
        formatted[name] = value
    return formatted
