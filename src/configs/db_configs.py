from pydantic_settings import BaseSettings

class DbConfigs(BaseSettings): 
    DB_URL: str 

    class Config:
        env_file = ".env"  
