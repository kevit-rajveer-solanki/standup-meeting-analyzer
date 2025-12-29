import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
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
        # The @lru_cache decorator is a good alternative here,
        # but a simple function call is sufficient.
        settings = Settings()
        logger.info("Configuration loaded successfully.")
        return settings
    except ValueError as e:
        logger.error(f"FATAL: Missing or invalid environment variables. Details: {e}")
        # In a real-world scenario, you might want to exit the application
        # immediately, but here we'll re-raise to halt execution.
        raise


# Create a single, cached instance of the settings
settings = get_settings()
