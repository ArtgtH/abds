from datetime import date

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from energosbyt.errors import bad_parameter


def query_date(value: str | None, name: str) -> date:
    if value is None:
        raise bad_parameter(name)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise bad_parameter(name) from None


def nonnegative(value: str | None, name: str, default: int) -> int:
    if value is None:
        return default
    if not value.isdecimal():
        raise bad_parameter(name)
    return int(value)


async def validation_error(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    issue = error.errors()[0]
    location = issue["loc"]
    if len(location) > 1 and location[0] == "body":
        message = f'invalid "{location[1]}" field'
    elif len(location) > 1 and location[0] == "query":
        message = f'invalid "{location[1]}" parameter'
    else:
        message = "invalid request body"
    return JSONResponse(status_code=400, content={"message": message})
