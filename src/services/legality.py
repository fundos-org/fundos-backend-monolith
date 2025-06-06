from typing import Any, Dict
from src.configs.configs import legality_configs

#  Note : header -> key : X-Auth-Token 


class LegalityService:
    def __init__(self):
        self.auth_token = legality_configs.auth_token
        self.salt = legality_configs.salt 

    async def send_document_for_signing(
        self, 
        user_id: str, 
    ) -> Dict[str, Any]:
        
        pass 
        