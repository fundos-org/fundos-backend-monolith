from fastapi import Request
import time
import json

from src.logging.logging_setup import get_logger  # import your own get_logger

logger = get_logger("request-logger")

async def log_request_data(request: Request) -> dict:
    try:
        body_bytes = await request.body()
        body = body_bytes.decode('utf-8')
        return json.loads(body) if body else {}
    except Exception:
        return {}

async def log_response_data(response) -> dict:
    try:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        return json.loads(body.decode('utf-8'))
    except Exception:
        return {}

async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()

    request_info = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "body": await log_request_data(request),
    }

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        logger.info(
            {
                "event": "request",
                "request": request_info,
                "response_status": response.status_code,
                "process_time_ms": f"{process_time:.2f}",
            }
        )
        return response

    except Exception as exc:
        logger.exception(
            {
                "event": "exception",
                "request": request_info,
                "error": str(exc)
            }
        )
        raise exc
