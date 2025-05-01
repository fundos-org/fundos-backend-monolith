# utils/exception_handlers.py

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette import status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "isSuccess": False,
            "message": "An unexpected error occurred. Please try again later.",
        }
    )

def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "isSuccess": False,
            "message": "Validation error",
            "details": exc.errors(),
        }
    )

def db_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "isSuccess": False,
            "message": "A database error occurred. Please try again later.",
        }
    )

def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "isSuccess": False,
            "message": exc.detail
        }
    )