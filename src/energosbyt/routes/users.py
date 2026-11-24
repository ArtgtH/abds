from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response

from energosbyt.database import insert, one
from energosbyt.errors import not_found
from energosbyt.schemas import UserPatch

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: int) -> dict:
    user = one(
        "SELECT id, fio, phone, phone_prev FROM dim_users FINAL "
        "WHERE id = {id:UInt64} LIMIT 1",
        {"id": user_id},
    )
    if user is None:
        raise not_found()
    return user


@router.patch("/{user_id}", status_code=204)
def patch_user(user_id: int, changes: UserPatch) -> Response:
    user = one(
        "SELECT id, fio, phone, phone_prev, created_at, updated_at "
        "FROM dim_users FINAL WHERE id = {id:UInt64} LIMIT 1",
        {"id": user_id},
    )
    if user is None:
        raise not_found()

    phone = changes.phone if changes.phone is not None else user["phone"]
    previous_phone = user["phone"] if phone != user["phone"] else user["phone_prev"]
    updated_at = max(
        datetime.now(UTC).replace(tzinfo=None),
        user["updated_at"] + timedelta(seconds=1),
    )
    insert(
        "dim_users",
        ["id", "fio", "phone", "phone_prev", "created_at", "updated_at"],
        [
            user_id,
            changes.fio or user["fio"],
            phone,
            previous_phone,
            user["created_at"],
            updated_at,
        ],
    )
    return Response(status_code=204)
