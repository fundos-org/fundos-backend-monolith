from pydantic_settings import BaseSettings

class AppConfigs(BaseSettings): 
    PORT: int 
    DEBUG: bool

    class Config:
        env_file = ".env"




