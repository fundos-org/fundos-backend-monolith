from src.models.user import User  # noqa: F401
from src.models.deal import Deal  # noqa: F401
from src.models.investment import Investment  # noqa: F401
from src.models.kyc import KYC  # noqa: F401

# Optional: if using a custom metadata object, but not strictly required for basic setup
# from sqlalchemy import MetaData
# metadata_obj = MetaData()
# SQLModel.metadata = metadata_obj

# No need to manually assign tables, SQLModel handles this
models = [Deal, Investment, KYC, User]


