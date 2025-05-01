from fastapi.responses import JSONResponse
from starlette import status

def success_response(message: str, data: dict = None, status_code: int = status.HTTP_200_OK):
    return JSONResponse(
        status_code=status_code,
        content={
            "isSuccess": True,
            "message": message,
            "data": data or {}
        }
    )

def error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    return JSONResponse(
        status_code=status_code,
        content={
            "isSuccess": False,
            "message": message
        }
    )
