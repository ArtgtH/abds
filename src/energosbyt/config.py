import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    port: int = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
    user: str = os.getenv("CLICKHOUSE_USER", "default")
    password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    database: str = os.getenv("CLICKHOUSE_DATABASE", "energosbyt")


settings = Settings()
