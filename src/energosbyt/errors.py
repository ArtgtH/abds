from fastapi import HTTPException


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="Not found")


def bad_field(name: str) -> HTTPException:
    return HTTPException(status_code=400, detail=f'invalid "{name}" field')


def bad_parameter(name: str) -> HTTPException:
    return HTTPException(status_code=400, detail=f'invalid "{name}" parameter')
