from threading import local
from typing import Any

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from energosbyt.config import settings

_thread_state = local()


def client() -> Client:
    current = getattr(_thread_state, "client", None)
    if current is None:
        current = clickhouse_connect.get_client(
            host=settings.host,
            port=settings.port,
            username=settings.user,
            password=settings.password,
            database=settings.database,
        )
        _thread_state.client = current
    return current


def rows(sql: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    result = client().query(sql, parameters=parameters or {})
    return [dict(zip(result.column_names, record)) for record in result.result_rows]


def one(sql: str, parameters: dict[str, Any] | None = None) -> dict[str, Any] | None:
    result = rows(sql, parameters)
    return result[0] if result else None


def insert(table: str, columns: list[str], record: list[Any]) -> None:
    client().insert(table, [record], column_names=columns)
