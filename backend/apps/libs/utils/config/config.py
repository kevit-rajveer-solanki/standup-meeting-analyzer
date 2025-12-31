import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Settings class for loading environment variables.
    Utilizes pydantic-settings to load from a .env file and validate.
    """
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_TENANT_ID: str
    MONGO_URI: str
    MONGO_DB_NAME: str
    GRAPH_SCOPE: str = "https://graph.microsoft.com/.default"
    HOST: str
    FASTAPI_PORT: int
    BACKEND_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )


def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    Fails fast if required environment variables are missing.
    """
    try:
        settings = Settings()
        logger.info("Configuration loaded successfully.")
        return settings
    except ValueError as e:
        logger.error(f"FATAL: Missing or invalid environment variables. Details: {e}")
        raise


settings = get_settings()
