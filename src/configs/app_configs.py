from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfigs(BaseSettings):
    ENV: str = "DEV"
    PORT: str = "8000"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
config = AppConfigs()