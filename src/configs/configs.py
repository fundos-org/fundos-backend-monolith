from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class AppConfigs(BaseSettings):
    env: str = "DEV"
    port: str = "8000"
    debug: bool = True
    host: str = "0.0.0.0"
    version: str = "v1_05_June_2025"
    apk_link: str = "http://43.205.36.168/api/v1/live/release/app"
    

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
    aws_region: str = "ap-south-1"
    aws_bucket: str = "fundos-dev-bucket"
    aws_deals_folder: str = "subadmin/deals"
    aws_profile_pictures_folder: str = "users/profile_pictures"
    aws_subadmin_profile_pictures_folder: str = "subadmin/profile_pictures"
    aws_mca_folder: str = "users/mca_documents"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
aws_config = AwsConfigs()

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
    from_email: str = "noreply@fundos.solutions"
    smtp_server: str = "smtp.zeptomail.in"
    smtp_port_tls: int = 587
    smtp_port_ssl: int = 465
    smtp_username: str = "emailapikey"
    smtp_password: str = "PHtE6r0IQe26iWB59BQG7KC7Q8akM417r7k2JFYVt9tKC/cGTE0A+o95m2TmoxwrUPATRvbOydhqs+uV4b3TIW7qND5IXWqyqK3sx/VYSPOZsbq6x00btVkSdUzbU47vctZp3CHRudffNA=="

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

# Usage
mail_configs = MailConfigs()

class ZohoConfigs(BaseSettings):
    zoho_client_id: str = "1000.HV5DRVU8JJN4QDSSX2UG24TU5539SK"
    zoho_client_secret: str = "789827012f3380e26d0408648b7f4d702cfd8bf995"
    zoho_refresh_token: str = "1000.fdcc4342e7597414eed476837c2dbebe.03c4d33175919ce6dea6907551d1c447"
    zoho_redirect_uri: str = "https%3A%2F%2Fsign.zoho.com"
    zoho_grant_type: str = "refresh_token"
    drawdown_template_id: str = "80016000000209107"
    contribution_template_id: str = "80016000000197395"
    zoho_base_url: str = "https://sign.zoho.in/api/v1"
    zoho_auth_url: str = "https://accounts.zoho.in/oauth/v2/token"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

zoho_configs = ZohoConfigs()

class MSG91Configs(BaseSettings):
    msg91_authkey: str = "453616AKdWaDgFt6833fe3bP1"
    msg91_signup_template_id: str = "683bf6d4d6fc05320619bde2"
    msg91_signin_template_id: str = "6839be0ed6fc05746f76b593"
    msg91_otp_api: str = "https://control.msg91.com/api/v5/otp"
    msg91_verify_api: str = "https://control.msg91.com/api/v5/otp/verify"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

msg91_configs = MSG91Configs() 

class RedisConfigs(BaseSettings):
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_cache_ttl: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

redis_configs = RedisConfigs()

class DigitapConfigs(BaseSettings):
    digitap_base_url: str = "https://svc.digitap.ai"
    validation_base_url: str = "https://svc.digitap.ai/validation"
    client_id: str = "17137231"
    client_secret: str = "RhoLU35zsKc2OMao9SNec3kpcHJjIWAk"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

digitap_configs = DigitapConfigs()

class LegalityConfigs(BaseSettings): 
    auth_token: str = "69XqrirsJOG2wFKRARq6WOeqPOEl29ko"
    salt: str = "fJSi3msagYOWIXJOPbrhGxuEgkoztG4G"
    profile_id: str = "QJxuqWt"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=True,
        extra="ignore"
    )

legality_configs = LegalityConfigs()