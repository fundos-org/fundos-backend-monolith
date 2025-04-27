from typing import List
from pydantic import BaseModel 

db: List[dict] = [
            {
                "iswar" : {
                    "school" : "dav",
                    "college" : "nitr",
                    "company" : "accenture" 
                }
            }, 
            {
                "gautam" : {
                    "school" : "dav",
                    "college" : "vssut", 
                    "company" : "accenture" 
                }
            }
        ]

class DbServices(BaseModel): 
    async def fetch_all_users() -> List[dict]: 
        try:
            return db
        except Exception as e: 
            return [{"error": e, "actual_error": "no records in db yet :("}]

    async def query_db(user_id: str) -> dict:
        try: 
            if user_id in db:
                return db[user_id]

        except KeyError as error : 
            return {"message": error, "actual_error": f"there is no record in db for {user_id}"}