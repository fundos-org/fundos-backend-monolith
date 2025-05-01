from pydantic_settings import BaseSettings
from typing import Dict, Any
from pydantic import field_validator

class AppEnvironment(BaseSettings):
    PORT: str = "8000"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    DB_URL: str = "sqlite:///db.sqlite"
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = True

class AppConfigs(BaseSettings):
    # Required fields that were missing
    DEV: Dict[str, Any] = {
        "PORT": "8000",
        "DEBUG": True,
        "HOST": "0.0.0.0",
        "DB_URL": "sqlite:///db.sqlite"
    }
    
    PROD: Dict[str, Any] = {
        "PORT": "8000",
        "DEBUG": False,
        "HOST": "0.0.0.0",
        "DB_URL": "sqlite:///db.sqlite"
    }
    
    # Set default values for configuration
    ENV: str = "DEV"
    PORT: str = "8000"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    DB_URL: str = "sqlite:///db.sqlite"
    
    @field_validator('ENV')
    def validate_env(cls, v):
        if v not in ['DEV', 'PROD']:
            raise ValueError('ENV must be either DEV or PROD')
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = True