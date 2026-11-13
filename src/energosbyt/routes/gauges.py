from datetime import UTC, datetime

from fastapi import APIRouter, Response

from energosbyt.database import insert, one
from energosbyt.errors import not_found
from energosbyt.routes.realty import require_realty
from energosbyt.schemas import GaugeInstall

router = APIRouter(prefix="/realty/{realty_id}/gauges", tags=["gauges"])

_COLUMNS = ["gauge_id", "realty_id", "created_at", "sign", "version"]


@router.post("", status_code=201)
def install_gauge(realty_id: int, installation: GaugeInstall) -> Response:
    require_realty(realty_id)
    if (
        one(
            "SELECT id FROM dim_gauges WHERE id = {id:UInt64} LIMIT 1",
            {"id": installation.gauge_id},
        )
        is None
    ):
        raise not_found()

    active = one(
        "SELECT gauge_id, created_at, version FROM fact_gauge_bindings FINAL "
        "WHERE realty_id = {id:UInt64} AND sign = 1 "
        "ORDER BY version DESC LIMIT 1",
        {"id": realty_id},
    )
    version = 1 if active is None else active["version"] + 1
    if active is not None:
        insert(
            "fact_gauge_bindings",
            _COLUMNS,
            [
                active["gauge_id"],
                realty_id,
                active["created_at"],
                -1,
                active["version"],
            ],
        )
    insert(
        "fact_gauge_bindings",
        _COLUMNS,
        [
            installation.gauge_id,
            realty_id,
            datetime.now(UTC).replace(tzinfo=None),
            1,
            version,
        ],
    )
    return Response(status_code=201)
