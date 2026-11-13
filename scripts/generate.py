"""Generate deterministic CSV fixtures without loading them into memory."""

import csv
from contextlib import ExitStack
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FIRST_DAY = date(2023, 11, 1)
LAST_DAY = date(2026, 10, 31)
REPLACEMENT_DAY = date(2024, 1, 1)
TARIFF_CHANGE_DAY = date(2025, 11, 1)
OBJECT_COUNT = 1_000
REPLACED_COUNT = 50

COLUMNS = {
    "dim_realty": (
        "id",
        "address",
        "square",
        "type",
        "number",
        "rooms",
        "floor",
        "porch",
        "created_at",
    ),
    "dim_gauges": ("id", "name", "country", "created_at"),
    "dim_tariffs": (
        "id",
        "name",
        "price_day_kwph",
        "price_night_kwph",
        "valid_from",
        "valid_to",
        "created_at",
        "updated_at",
    ),
    "dim_users": ("id", "fio", "phone", "phone_prev", "created_at", "updated_at"),
    "fact_gauge_bindings": ("gauge_id", "realty_id", "created_at", "sign", "version"),
    "fact_meter_readings": (
        "realty_id",
        "user_id",
        "tariff_id",
        "gauge_id",
        "reading_date",
        "day_kw",
        "night_kw",
        "created_at",
    ),
    "fact_invoice": (
        "realty_id",
        "user_id",
        "tariff_id",
        "gauge_id",
        "day_kw",
        "night_kw",
        "price",
        "deadline",
        "created_at",
    ),
}


def writers(stack: ExitStack) -> dict[str, csv.writer]:
    DATA_DIR.mkdir(exist_ok=True)
    result = {}
    for table, columns in COLUMNS.items():
        file = stack.enter_context(
            (DATA_DIR / f"{table}.csv").open("w", newline="", encoding="utf-8")
        )
        writer = csv.writer(file)
        writer.writerow(columns)
        result[table] = writer
    return result


def gauge_for(object_id: int, day: date) -> int:
    if object_id <= REPLACED_COUNT and day >= REPLACEMENT_DAY:
        return OBJECT_COUNT + object_id
    return object_id


def generate_dimensions(out: dict[str, csv.writer]) -> None:
    created_at = "2023-11-01 10:00:00"
    for object_id in range(1, OBJECT_COUNT + 1):
        is_flat = object_id % 10 != 0
        out["dim_realty"].writerow(
            (
                object_id,
                f"г. Москва, улица Пушкина, дом {1 + (object_id - 1) // 100}",
                35 + object_id % 80,
                "flat" if is_flat else "nrcp",
                str(object_id) if is_flat else "",
                1 + object_id % 4 if is_flat else 0,
                1 + object_id % 20,
                1 + object_id % 4,
                created_at,
            )
        )
        out["dim_users"].writerow(
            (
                object_id,
                f"Иванов Иван {object_id}",
                f"+7900000{object_id:04d}",
                "",
                created_at,
                created_at,
            )
        )
        out["dim_gauges"].writerow((object_id, "Меркурий 234", "Россия", created_at))
        out["fact_gauge_bindings"].writerow((object_id, object_id, created_at, 1, 1))

    for object_id in range(1, REPLACED_COUNT + 1):
        replacement_id = OBJECT_COUNT + object_id
        out["dim_gauges"].writerow(
            (replacement_id, "Нева МТ 124", "Россия", created_at)
        )
        out["fact_gauge_bindings"].writerow((object_id, object_id, created_at, -1, 1))
        out["fact_gauge_bindings"].writerow(
            (
                replacement_id,
                object_id,
                "2024-01-01 10:00:01",
                1,
                2,
            )
        )

    out["dim_tariffs"].writerows(
        (
            (
                1,
                "День–Ночь",
                580,
                290,
                "2023-11-01 00:00:00",
                "2025-11-01 00:00:00",
                created_at,
                created_at,
            ),
            (
                1,
                "День–Ночь",
                620,
                310,
                "2025-11-01 00:00:00",
                "2099-01-01 00:00:00",
                created_at,
                "2025-11-01 10:00:00",
            ),
        )
    )


def generate_readings(out: csv.writer) -> None:
    day = FIRST_DAY
    while day <= LAST_DAY:
        reading_date = day.isoformat()
        for object_id in range(1, OBJECT_COUNT + 1):
            base = (
                object_id,
                object_id,
                1,
                gauge_for(object_id, day),
                reading_date,
                1000 + (object_id * 7 + day.toordinal()) % 900,
                300 + (object_id * 3 + day.toordinal()) % 500,
            )
            out.writerow((*base, f"{reading_date} 09:00:00"))
            if (object_id * 37 + day.toordinal()) % 100 < 3:
                out.writerow(
                    (
                        *base[:5],
                        base[5] + 1,
                        base[6] + 2,
                        f"{reading_date} 12:00:00",
                    )
                )
        day += timedelta(days=1)


def generate_invoices(out: csv.writer) -> None:
    month = FIRST_DAY
    for _ in range(36):
        next_month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
        day_price, night_price = (580, 290) if month < TARIFF_CHANGE_DAY else (620, 310)
        for object_id in range(1, OBJECT_COUNT + 1):
            day_kw, night_kw = 100 + object_id % 70, 40 + object_id % 35
            out.writerow(
                (
                    object_id,
                    object_id,
                    1,
                    gauge_for(object_id, month),
                    day_kw,
                    night_kw,
                    day_kw * day_price + night_kw * night_price,
                    next_month.replace(day=10).isoformat(),
                    f"{month.isoformat()} 10:00:00",
                )
            )
        month = next_month


def main() -> None:
    with ExitStack() as stack:
        out = writers(stack)
        generate_dimensions(out)
        generate_readings(out["fact_meter_readings"])
        generate_invoices(out["fact_invoice"])
    print(f"Generated CSV files in {DATA_DIR}")


if __name__ == "__main__":
    main()
