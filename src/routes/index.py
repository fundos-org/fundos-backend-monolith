from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.db_services import DbServices

router = APIRouter() 


# @router.get('/')
# async def 

@router.get('/fetch/{user_id}')
async def fetch_something(user_id): 
    data = await DbServices.query_db(user_id)
    content: dict = {"isSuccess":"ok", "data" : data}
    return JSONResponse(status_code=200, content = content)
    
@router.get("/fetch-all")
async def fetch_all_records():
    data = await DbServices.fetch_all_users() 
    content: dict = {"isSuccess": "ok", "data" : data}
    return JSONResponse(status_code=200, content=content)