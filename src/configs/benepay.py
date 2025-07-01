from pydantic_settings import BaseSettings, SettingsConfigDict 

class BenePayConfigs(BaseSettings): 
    client_id: str = "2bm1d6iong8q5o031ps1l3fhll"
    client_secret: str = "hhradhls5vk5a402j9qus4otc40ldghpsjjcbv3shg46en7q6io"
    base_url: str = ""
    api_key: str = "m0OKyFypSF9Ndc8dLN8CW5QsKBWY0JoE7cYQNndb"
    auth_url: str = "https://bene-collect.auth.eu-west-2.amazoncognito.com/oauth2/token"
    pay_url: str = "https://uat-api-collect-payment.benepay.io/v1/realTimeRequestToPay"
    encryption_key: str = "4913DC47A9B59B46F4D83BA9E157F33AF534001A11290F9DF60B2C3C323A4AB1"
    comments: str = "Add Comments"
    charges: int = 0
    charges_reason: str = "OnlinePayment"
    return_url: str = "https://api.fundos.services"
    merchant_id: str = "Demo"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="db",
        case_sensitive=True,
        extra="ignore"
    )

benepay_configs = BenePayConfigs()