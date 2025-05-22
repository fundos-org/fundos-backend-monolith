from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfigs(BaseSettings):
    env: str = "DEV"
    PORT: str = "8000"
    debug: bool = True
    host: str = "0.0.0.0"
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
app_config = AppConfigs() 

class DbConfigs(BaseSettings): 
    user: str = "fundos"
    password: str = "Tx2ESTRpEmcpHmnD3UyP"
    host: str = "aws-postgres.cnqyumwq0t3u.ap-south-1.rds.amazonaws.com"
    port: int = 5432
    dbname: str = "postgres"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="db",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
db_config = DbConfigs()

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
aws_config = AwsConfigs()

# class RedisConfigs(BaseSettings): 
#     redis_url: str
#     redis_port: int
#     redis_db: int
#     redis_password: str

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_prefix="",
#         case_sensitive=True,
#         extra="ignore"
#     )

# # Usage 
# redis_config = RedisConfigs()

class PaymentConfigs(BaseSettings):
    api_key: str = "c7036088-4387-4e56-b3dc-e3f81642fd70"
    salt: str = "4f738d43bedc00376816fb2050fd347602cf0cac"
    base_url: str = "https://mystore.payaidpayments.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
payment_configs = PaymentConfigs()

class MailConfigs(BaseSettings):
    zeptomail_api_key: str = "Zoho-enczapikey PHtE6r0IQe26iWB59BQG7KC7Q8akM417r7k2JFYVt9tKC/cGTE0A+o95m2TmoxwrUPATRvbOydhqs+uV4b3TIW7qND5IXWqyqK3sx/VYSPOZsbq6x00btVkSdUzbU47vctZp3CHRudffNA=="
    from_email: str = "noreply@fundos.solutions"
    zeptomail_url: str = "https://api.zeptomail.com/v1.1/email"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
mail_configs = MailConfigs()

