from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter() 

@router.get('/health')
def health():
    content = {"isSuccess": "ok", "message": "router setup done."}
    return JSONResponse(status_code=200, content=content) 