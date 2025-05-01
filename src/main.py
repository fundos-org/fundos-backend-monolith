from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.configs.app_configs import AppConfigs
from src.routes.index import router as indexRouter
from src.routes.kyc import router as kycRouter
from src.routes.deals import router as dealsRouter
from src.middlewares.request_logger import request_logging_middleware
from src.utils.lifespan import lifespan
from src.middlewares.exception_handlers import (
    general_exception_handler,
    validation_exception_handler,
    http_exception_handler,
)

version = "v1"
api_prefix = "/api/v1"
app = FastAPI(lifespan=lifespan) 

# Register the middleware using FastAPI's .middleware() method
app.middleware("http")(request_logging_middleware) 

# adding exception handling 
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# adding api Routers 
app.include_router(router=indexRouter, prefix=f"{api_prefix}", tags=["index"])
app.include_router(router=kycRouter, prefix=f"{api_prefix}/kyc", tags=["kyc"])
app.include_router(router=dealsRouter, prefix=f"{api_prefix}/deals", tags=["deals"])

app_configs = AppConfigs()
port = 8000

@app.get("/")
async def root(): 
    return JSONResponse(status_code=200, content= {"message" : f"app running on localhost:{port}", "isSuccess": True})





