from pydantic_settings import BaseSettings, SettingsConfigDict

class AwsConfigs(BaseSettings): 
    aws_region: str
    aws_bucket: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
config = AwsConfigs()