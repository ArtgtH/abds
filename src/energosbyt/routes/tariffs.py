from fastapi import APIRouter, Request

from energosbyt.database import one
from energosbyt.errors import not_found
from energosbyt.formatting import format_row
from energosbyt.validation import query_date

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.get("")
def get_tariff(request: Request) -> dict:
    lookup_date = query_date(request.query_params.get("date"), "date")
    tariff = one(
        "SELECT id, name, price_day_kwph, price_night_kwph, valid_from, valid_to "
        "FROM dim_tariffs FINAL WHERE valid_from <= {date:Date} "
        "AND {date:Date} < valid_to ORDER BY valid_from DESC LIMIT 1",
        {"date": lookup_date},
    )
    if tariff is None:
        raise not_found()
    return format_row(tariff)
