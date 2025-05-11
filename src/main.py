from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.configs.app_configs import AppConfigs
from src.routes.index import router as indexRouter
from src.routes.kyc import router as kycRouter
from src.routes.deal import router as dealsRouter 
from src.routes.dummy import router as dummyRouter
from src.routes.onboarding import router as onBoardingRouter
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

# from src.middlewares.request_logger import request_logging_middleware
# Register the middleware using FastAPI's .middleware() method
# app.middleware("http")(request_logging_middleware) 

# Handle cors middle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# adding exception handling 
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# adding api Routers 
app.include_router(router=indexRouter, prefix=f"{api_prefix}", tags=["index"])
app.include_router(router=kycRouter, prefix=f"{api_prefix}/kyc", tags=["kyc"])
app.include_router(router=dealsRouter, prefix=f"{api_prefix}/deals", tags=["deals"]) 
app.include_router(router=onBoardingRouter, prefix=f"{api_prefix}/onboarding", tags=["live"])

# dummy api Routers
app.include_router(router=dummyRouter, prefix=f"{api_prefix_v0}", tags=["test"])

app_configs = AppConfigs()
port = 8000

@app.get("/")
async def root(): 
    return JSONResponse(status_code=200, content= {"message" : f"app running on localhost:{port}", "isSuccess": True})





