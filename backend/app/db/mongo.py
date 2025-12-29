import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)


class MongoManager:
    """
    Manages the connection to MongoDB and provides access to the database.
    """

    def __init__(self):
        self.client: MongoClient = None
        self.db = None

    def connect(self):
        """
        Establishes the connection to the MongoDB server and database.
        """
        try:
            self.client = MongoClient(settings.MONGO_URI)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            self.db = self.client[settings.MONGO_DB_NAME]
            logger.info(f"Successfully connected to MongoDB database: {settings.MONGO_DB_NAME}")
        except ConnectionFailure as e:
            logger.error(f"FATAL: Could not connect to MongoDB. Details: {e}")
            raise

    def disconnect(self):
        """
        Closes the connection to MongoDB.
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")


# Singleton instance for the database manager
mongo_manager = MongoManager()


def get_db():
    """
    Dependency injector for FastAPI to get the database instance.
    This is a simple implementation. For production, you might use
    a connection pool and manage connections per request.
    """
    if mongo_manager.db is None:
        # This will be called on application startup
        raise RuntimeError("Database connection has not been initialized.")
    return mongo_manager.db
