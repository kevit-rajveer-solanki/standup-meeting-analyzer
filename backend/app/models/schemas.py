from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class StandupMeetingConfig(BaseModel):
    """
    Pydantic model for the 'standup_meetings' collection document.
    """
    project_tag: str = Field(..., description="A unique identifier for the project.")
    organizer_email: str = Field(..., description="The email of the meeting organizer.")
    meeting_link: str = Field(..., description="The MS Teams meeting join link.")
    is_active: bool = Field(default=True, description="Whether this configuration is currently active.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # This allows the model to be created from MongoDB documents (which use _id)
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "project_tag": "DRVN101",
                "organizer_email": "manager@company.com",
                "meeting_link": "https://teams.microsoft.com/...",
                "is_active": True,
            }
        }


class AnalysisRequest(BaseModel):
    """
    Model for the incoming analysis request from the frontend.
    The token, organizer email, and meeting link are removed.
    """
    project_tag: str
    start_date: str
    end_date: str

class ProjectTag(BaseModel):
    project_tag: str
