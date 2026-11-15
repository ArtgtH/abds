from fastapi import APIRouter, Request

from energosbyt.database import one, rows
from energosbyt.formatting import format_row
from energosbyt.routes.realty import require_realty
from energosbyt.validation import nonnegative

router = APIRouter(prefix="/realty/{realty_id}/invoices", tags=["invoices"])


@router.get("")
def list_invoices(realty_id: int, request: Request) -> dict:
    limit = nonnegative(request.query_params.get("limit"), "limit", 10)
    offset = nonnegative(request.query_params.get("offset"), "offset", 0)
    require_realty(realty_id)
    count = one(
        "SELECT count() AS count FROM fact_invoice WHERE realty_id = {id:UInt64}",
        {"id": realty_id},
    )["count"]
    invoices = rows(
        "SELECT tariff_id, gauge_id, day_kw, night_kw, price, deadline, created_at "
        "FROM fact_invoice WHERE realty_id = {id:UInt64} "
        "ORDER BY created_at DESC LIMIT {limit:UInt64} OFFSET {offset:UInt64}",
        {"id": realty_id, "limit": limit, "offset": offset},
    )
    return {"invoices": [format_row(invoice) for invoice in invoices], "count": count}
