# src/logging/logging_middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from src.logging.logging_setup import get_logger  # or wherever your get_logger is defined
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware_logger")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get handler module (if available)
        endpoint = request.scope.get("endpoint")
        module_name = getattr(endpoint, "__module__", "unknown")

        try:
            request_body = await request.body()
            request_data = request_body.decode("utf-8") if request_body else None
        except Exception:
            request_data = "<failed to read body>"

        try:
            response = await call_next(request)
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            duration = round((time.time() - start_time) * 1000, 2)

            # Recreate response object since we consumed it
            final_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            self.logger.info({
                "event": "http",
                "method": request.method,
                "url": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
                "request_body": request_data,
                "response_body": response_body.decode("utf-8"),
                "module": module_name
            })

            return final_response
        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            self.logger.exception({
                "event": "error",
                "method": request.method,
                "url": request.url.path,
                "request_body": request_data,
                "duration_ms": duration,
                "module": module_name,
                "error": str(e)
            })
            raise e
