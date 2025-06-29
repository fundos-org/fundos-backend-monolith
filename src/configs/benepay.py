from pydantic_settings import BaseSettings, SettingsConfigDict 

class BenePayConfigs(BaseSettings): 
    client_id: str = " "
    client_secret: str = " "
    base_url: str = " "
    api_key: str = " "
    auth_url: str = "https://bene-collect.auth.eu-west-2.amazoncognito.com/oauth2/token"
    pay_url: str = "https://uat-api-collect-payment.benepay.io/v1/realTimeRequestToPay"
    encryption_key: str = " "


    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="db",
        case_sensitive=True,
        extra="ignore"
    )

benepay_configs = BenePayConfigs()