.PHONY: run stop gen load setup teardown clean
.DEFAULT_GOAL := run

include .env.local
export CLICKHOUSE_HOST CLICKHOUSE_HTTP_PORT CLICKHOUSE_USER CLICKHOUSE_PASSWORD CLICKHOUSE_DATABASE

run:
	docker compose --env-file .env.local up -d --build

stop:
	docker compose --env-file .env.local down

gen:
	python3 scripts/generate.py

load:
	python3 scripts/database.py create
	python3 scripts/database.py load

setup: gen load

teardown:
	python3 scripts/database.py drop

clean:
	docker compose --env-file .env.local down -v
