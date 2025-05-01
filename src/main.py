from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from configs.app_configs import AppConfigs
from routes.index import router as indexRouter
from routes.kyc import router as kycRouter
from routes.deals import router as dealsRouter
from middlewares.request_logger import request_logging_middleware
from utils.lifespan import lifespan
from middlewares.exception_handlers import (
    general_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    db_exception_handler,
)

app = FastAPI(lifespan=lifespan) 

# Register the middleware using FastAPI's .middleware() method
app.middleware("http")(request_logging_middleware) 

# adding exception handling 
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, db_exception_handler)

# adding api Routers 
app.include_router(router=indexRouter, prefix="/api/v1")
app.include_router(router=kycRouter, prefix="/api/v1/kyc")
app.include_router(router=dealsRouter, prefix="/api/v1/deals")

app_configs = AppConfigs()

@app.get("/")
async def root(): 
    return JSONResponse(status_code=200, content= {"message" : f"app running on localhost:{app_configs.PORT}", "isSuccess": True})

@app.get("/db")
async def db_details():
    return JSONResponse(status_code=200, content= f"db url: {app_configs.DB_URL}")




