from fastapi import APIRouter

from energosbyt.database import one
from energosbyt.errors import not_found

router = APIRouter(prefix="/realty", tags=["realty"])


def require_realty(realty_id: int) -> None:
    exists = one(
        "SELECT id FROM dim_realty WHERE id = {id:UInt64} LIMIT 1",
        {"id": realty_id},
    )
    if exists is None:
        raise not_found()


@router.get("/{realty_id}")
def get_realty(realty_id: int) -> dict:
    realty = one(
        "SELECT id, address, square, type, number, rooms, floor, porch "
        "FROM dim_realty WHERE id = {id:UInt64} LIMIT 1",
        {"id": realty_id},
    )
    if realty is None:
        raise not_found()
    return realty
