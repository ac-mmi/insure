"""API exception handlers."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.adjudication import AdjudicationError
from app.services.dispute import DisputeError
from app.services.exceptions import InvalidOperationError, NotFoundError


class ErrorResponse(BaseModel):
    detail: str


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(detail=exc.message).model_dump(),
        )

    @app.exception_handler(InvalidOperationError)
    async def invalid_operation_handler(
        _request: Request, exc: InvalidOperationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(detail=exc.message).model_dump(),
        )

    @app.exception_handler(AdjudicationError)
    async def adjudication_error_handler(
        _request: Request, exc: AdjudicationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(detail=str(exc)).model_dump(),
        )

    @app.exception_handler(DisputeError)
    async def dispute_error_handler(_request: Request, exc: DisputeError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(detail=str(exc)).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        messages = []
        for error in errors:
            location = " -> ".join(str(part) for part in error["loc"])
            messages.append(f"{location}: {error['msg']}")
        detail = "; ".join(messages)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(detail=detail).model_dump(),
        )
