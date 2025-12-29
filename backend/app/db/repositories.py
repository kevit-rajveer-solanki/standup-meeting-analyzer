import logging
from pymongo.database import Database
from pymongo import ASCENDING
from pymongo.errors import PyMongoError
from typing import List, Optional

from ..models.schemas import StandupMeetingConfig, ProjectTag, ProjectCreate, ProjectUpdate
from datetime import datetime
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
    
    def get_all_projects(self) -> List[StandupMeetingConfig]:
        """
        Fetches all project configurations.

        Returns:
            A list of StandupMeetingConfig objects.
        """
        projects = []
        try:
            cursor = self.collection.find({})
            for doc in cursor:
                projects.append(StandupMeetingConfig(**doc))
        except PyMongoError as e:
            logger.error(f"Database error while fetching all projects: {e}")
        return projects

    def create_project(self, project: ProjectCreate) -> Optional[StandupMeetingConfig]:
        """
        Creates a new project configuration.

        Args:
            project: The project details.

        Returns:
            The created project configuration or None if it fails.
        """
        try:
            now = datetime.utcnow()
            new_project = self.collection.insert_one({
                "project_tag": project.project_tag,
                "organizer_email": project.organizer_email,
                "meeting_link": project.meeting_link,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            })
            if new_project.inserted_id:
                created_doc = self.collection.find_one({"_id": new_project.inserted_id})
                return StandupMeetingConfig(**created_doc)
        except PyMongoError as e:
            logger.error(f"Database error while creating project '{project.project_tag}': {e}")
        return None

    def update_project(self, project_tag: str, project_update: ProjectUpdate) -> Optional[StandupMeetingConfig]:
        """
        Updates an existing project configuration.

        Args:
            project_tag: The tag of the project to update.
            project_update: The fields to update.

        Returns:
            The updated project configuration or None if it fails.
        """
        update_data = {k: v for k, v in project_update.model_dump().items() if v is not None}
        if not update_data:
            return self.get_project_by_tag(project_tag) # Nothing to update

        update_data["updated_at"] = datetime.utcnow()

        try:
            result = self.collection.find_one_and_update(
                {"project_tag": project_tag},
                {"$set": update_data},
                return_document=True
            )
            if result:
                return StandupMeetingConfig(**result)
        except PyMongoError as e:
            logger.error(f"Database error while updating project '{project_tag}': {e}")
        return None

    def delete_project(self, project_tag: str) -> bool:
        """
        Deletes a project configuration.

        Args:
            project_tag: The tag of the project to delete.

        Returns:
            True if deleted, False otherwise.
        """
        try:
            result = self.collection.delete_one({"project_tag": project_tag})
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Database error while deleting project '{project_tag}': {e}")
        return False
