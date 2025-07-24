from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from src.routes.kyc import router as kycRouter
from src.routes.deal import router as dealsRouter 
from src.routes.dummy import router as dummyRouter
from src.routes.admin import router as adminRouter
from src.routes.subadmin import router as subadminRouter
from src.routes.release import router as releaseRouter
from src.routes.index import router as indexRouter
from src.routes.v2.kyc import router as KycRouterV2
from src.routes.v2.payments import router as paymentsRouterV2
from src.utils.lifespan import lifespan
from src.middlewares.exception_handlers import (
    general_exception_handler,
    validation_exception_handler,
    http_exception_handler,
)
from fastapi.middleware.cors import CORSMiddleware


api_prefix_v1 = "/api/v1/live" 
api_prefix_v0 = "/api/v0/test" 
api_prefix_v2 = "/api/v2/live"

app = FastAPI(lifespan=lifespan) 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add logging middleware
# app.add_middleware(LoggingMiddleware)

# adding exception handling 
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# Mount v1 api routers 
app.include_router(router=indexRouter, tags=["index"])
app.include_router(router=kycRouter, prefix=f"{api_prefix_v1}/kyc", tags=["investor"])
app.include_router(router=dealsRouter, prefix=f"{api_prefix_v1}/deals", tags=["deals"]) 
app.include_router(router=adminRouter, prefix=f"{api_prefix_v1}/admin", tags=["admin"])
app.include_router(router=subadminRouter, prefix=f"{api_prefix_v1}/subadmin", tags=["subadmin"])
app.include_router(router=releaseRouter, prefix=f"{api_prefix_v1}/release", tags=["release"])


# Mount v0 api routers
app.include_router(router=dummyRouter, prefix=f"{api_prefix_v0}", tags=["test", "investor"])

# Mount v2 api routers 
app.include_router(router=KycRouterV2, prefix=f"{api_prefix_v2}/kyc", tags=["investor_v2"])
app.include_router(router=paymentsRouterV2, prefix=f"{api_prefix_v2}/payments", tags=["payment_v2"])

# Add CORS middleware if needed








