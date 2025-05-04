from pydantic_settings import BaseSettings, SettingsConfigDict

class DbConfigs(BaseSettings): 
    DB_URL: str = "sqlite:///db.sqlite"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
config = DbConfigs()
