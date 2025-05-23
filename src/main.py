from fastapi import FastAPI
from fastapi.responses import JSONResponse
from configs.app_configs import AppConfigs
from routes.index import router as indexRouter
from routes.kyc import router as kycRouter
from middlewares.request_logger import request_logging_middleware
from utils.lifespan import lifespan

app = FastAPI(lifespan=lifespan) 
# Register the middleware using FastAPI's .middleware() method
app.middleware("http")(request_logging_middleware) 

app.include_router(router=indexRouter, prefix="/api/v1")
app.include_router(router=kycRouter, prefix="/api/v1/kyc")

app_configs = AppConfigs()

@app.get("/")
async def root(): 
    return JSONResponse(status_code=200, content= {"message" : f"app running on localhost:{app_configs.PORT}", "isSuccess": True})

@app.get("/db")
async def db_details():
    return JSONResponse(status_code=200, content= f"db url: {app_configs.DB_URL}")




