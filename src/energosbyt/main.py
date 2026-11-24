import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from energosbyt.routes import gauges, invoices, readings, realty, tariffs, users
from energosbyt.validation import validation_error

app = FastAPI(title="ЭнергоСбыт")
app.add_exception_handler(RequestValidationError, validation_error)
logger = logging.getLogger(__name__)


@app.exception_handler(HTTPException)
async def http_error(_request: Request, error: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code, content={"message": error.detail}
    )


@app.exception_handler(Exception)
async def unexpected_error(_request: Request, error: Exception) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=error)
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


@app.get("/ping")
def ping() -> Response:
    return Response(status_code=200)


for router in (
    users.router,
    realty.router,
    readings.router,
    invoices.router,
    tariffs.router,
    gauges.router,
):
    app.include_router(router)
