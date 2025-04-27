from pydantic_settings import BaseSettings

class AppConfigs(BaseSettings): 
    PORT: int 
    DEBUG: bool
    DEV: str
    PROD: str
    

    class Config:
        env_file = ".env"




