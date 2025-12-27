import logging
from pymongo.database import Database
from pymongo import ASCENDING
from pymongo.errors import PyMongoError
from typing import List, Optional

from app.models.schemas import StandupMeetingConfig, ProjectTag

# Configure logging
logger = logging.getLogger(__name__)

COLLECTION_NAME = "standup_meetings"


class ProjectRepository:
    """
    Handles all database operations for the 'standup_meetings' collection.
    """

    def __init__(self, db: Database):
        self.db = db
        self.collection = db[COLLECTION_NAME]

    def create_indexes(self):
        """
        Creates necessary indexes for the collection.
        Should be called on application startup.
        """
        try:
            self.collection.create_index([("project_tag", ASCENDING)], unique=True)
            logger.info(f"Indexes created successfully for collection '{COLLECTION_NAME}'.")
        except PyMongoError as e:
            logger.error(f"Error creating indexes for '{COLLECTION_NAME}': {e}")
            raise

    def get_project_by_tag(self, project_tag: str) -> Optional[StandupMeetingConfig]:
        """
        Fetches a single active project configuration by its tag.

        Args:
            project_tag: The unique tag of the project.

        Returns:
            A StandupMeetingConfig object or None if not found or inactive.
        """
        try:
            document = self.collection.find_one({"project_tag": project_tag, "is_active": True})
            if document:
                return StandupMeetingConfig(**document)
        except PyMongoError as e:
            logger.error(f"Database error while fetching project '{project_tag}': {e}")
        return None

    def get_all_active_projects(self) -> List[ProjectTag]:
        """
        Fetches the project tags for all active projects.

        Returns:
            A list of ProjectTag objects.
        """
        projects = []
        try:
            cursor = self.collection.find({"is_active": True}, {"project_tag": 1, "_id": 0})
            for doc in cursor:
                projects.append(ProjectTag(**doc))
        except PyMongoError as e:
            logger.error(f"Database error while fetching all active projects: {e}")

        return projects
