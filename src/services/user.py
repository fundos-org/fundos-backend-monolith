from fastapi import HTTPException
from src.logging.logging_setup import get_logger 

logger = get_logger(__name__)


class UserService:
    def __init__(self):
        self.bucket_name = ""
        self.folder_prefix = ""
  
    async def verify_invitation_code(invitation_code: str): 

        try: 
            if invitation_code == "fundos": 
                return {
                    "success": True, 
                } 
            
            else: 
                return {
                    "success": False, 
                }
        except Exception as e: 
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")