"""Create, load and remove ClickHouse tables for the lab."""

import argparse
import base64
import http.client
import os
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
TABLES = (
    "dim_realty",
    "dim_gauges",
    "dim_tariffs",
    "dim_users",
    "fact_gauge_bindings",
    "fact_meter_readings",
    "fact_invoice",
)
DATABASE = os.getenv("CLICKHOUSE_DATABASE", "energosbyt")
HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
USER = os.getenv("CLICKHOUSE_USER", "default")
PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")


def execute(sql: str, csv_path: Path | None = None) -> None:
    connection = http.client.HTTPConnection(HOST, PORT, timeout=180)
    params = urlencode({"database": DATABASE, "query": sql})
    credentials = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    try:
        if csv_path is None:
            connection.request("POST", f"/?{params}", headers=headers)
        else:
            headers["Content-Length"] = str(csv_path.stat().st_size)
            connection.putrequest("POST", f"/?{params}")
            for name, value in headers.items():
                connection.putheader(name, value)
            connection.endheaders()
            with csv_path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    connection.send(chunk)

        response = connection.getresponse()
        message = response.read().decode()
        if response.status != 200:
            raise RuntimeError(f"ClickHouse rejected {sql!r}: {message}")
    finally:
        connection.close()


def create() -> None:
    statements = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    for statement in statements.split(";"):
        if statement.strip():
            execute(statement.strip())


def load() -> None:
    for table in TABLES:
        path = ROOT / "data" / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Run 'make gen' first: {path} is missing")
    for table in TABLES:
        execute(f"TRUNCATE TABLE {DATABASE}.{table}")
    for table in TABLES:
        execute(
            f"INSERT INTO {DATABASE}.{table} FORMAT CSVWithNames",
            ROOT / "data" / f"{table}.csv",
        )
        print(f"Loaded {table}")


def drop() -> None:
    for table in reversed(TABLES):
        execute(f"DROP TABLE IF EXISTS {DATABASE}.{table}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("create", "load", "drop"))
    command = parser.parse_args().command
    {"create": create, "load": load, "drop": drop}[command]()


if __name__ == "__main__":
    main()
