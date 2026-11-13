from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request, Response

from energosbyt.database import insert, one, rows
from energosbyt.errors import bad_parameter, not_found
from energosbyt.formatting import format_row
from energosbyt.routes.realty import require_realty
from energosbyt.schemas import ReadingCreate
from energosbyt.validation import query_date

router = APIRouter(prefix="/realty/{realty_id}/readings", tags=["readings"])


@router.get("")
def list_readings(realty_id: int, request: Request) -> dict:
    start = query_date(request.query_params.get("date_from"), "date_from")
    end = query_date(request.query_params.get("date_to"), "date_to")
    if start > end:
        raise bad_parameter("date_from")
    require_realty(realty_id)
    readings = rows(
        "SELECT reading_date, user_id, tariff_id, gauge_id, day_kw, night_kw "
        "FROM fact_meter_readings FINAL WHERE realty_id = {id:UInt64} "
        "AND reading_date BETWEEN {start:Date} AND {end:Date} "
        "ORDER BY reading_date",
        {"id": realty_id, "start": start, "end": end},
    )
    return {
        "readings": [format_row(reading) for reading in readings],
        "count": len(readings),
    }


@router.post("", status_code=201)
def create_reading(realty_id: int, reading: ReadingCreate) -> Response:
    require_realty(realty_id)
    references = (
        ("dim_users FINAL", reading.user_id),
        ("dim_gauges", reading.gauge_id),
        ("dim_tariffs FINAL", reading.tariff_id),
    )
    for table, identifier in references:
        if (
            one(
                f"SELECT id FROM {table} WHERE id = {{id:UInt64}} LIMIT 1",
                {"id": identifier},
            )
            is None
        ):
            raise not_found()

    latest = one(
        "SELECT created_at FROM fact_meter_readings FINAL "
        "WHERE realty_id = {id:UInt64} AND reading_date = {date:Date} LIMIT 1",
        {"id": realty_id, "date": reading.reading_date},
    )
    created_at = datetime.now(UTC).replace(tzinfo=None)
    if latest is not None:
        created_at = max(created_at, latest["created_at"] + timedelta(seconds=1))
    insert(
        "fact_meter_readings",
        [
            "realty_id",
            "user_id",
            "tariff_id",
            "gauge_id",
            "reading_date",
            "day_kw",
            "night_kw",
            "created_at",
        ],
        [
            realty_id,
            reading.user_id,
            reading.tariff_id,
            reading.gauge_id,
            reading.reading_date,
            reading.day_kw,
            reading.night_kw,
            created_at,
        ],
    )
    return Response(status_code=201)
