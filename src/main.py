from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.logging.logging_middleware import LoggingMiddleware
from src.configs.configs import app_config
from src.routes.kyc import router as kycRouter
from src.routes.deal import router as dealsRouter 
from src.routes.dummy import router as dummyRouter
from src.routes.admin import router as adminRouter
from src.routes.subadmin import router as subadminRouter
from src.utils.lifespan import lifespan
from src.middlewares.exception_handlers import (
    general_exception_handler,
    validation_exception_handler,
    http_exception_handler,
)

version = "v1"
api_prefix = "/api/v1/live" 

version_v0 = "v0" 
api_prefix_v0 = "/api/v0/test" 

app = FastAPI(lifespan=lifespan) 

# add logging middleware
# app.add_middleware(LoggingMiddleware)

# adding exception handling 
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# health route 
@app.get("/health", tags=["index"])
async def health():
    return JSONResponse(
        status_code=200, 
        content={
            "message" : f"server is healthy and up and running on Port: {app_config.port}",
            "success": True, 
            "version": f"{app_config.version}"
            }
        )

# adding api Routers 
app.include_router(router=kycRouter, prefix=f"{api_prefix}/kyc", tags=["investor"])
app.include_router(router=dealsRouter, prefix=f"{api_prefix}/deals", tags=["deals"]) 
app.include_router(router=adminRouter, prefix=f"{api_prefix}/admin", tags=["admin"])
app.include_router(router=subadminRouter, prefix=f"{api_prefix}/subadmin", tags=["subadmin"])

# Test api Routers
app.include_router(router=dummyRouter, prefix=f"{api_prefix_v0}", tags=["test", "investor"])







