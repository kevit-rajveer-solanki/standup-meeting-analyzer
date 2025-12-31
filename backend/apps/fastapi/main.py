import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database

from .auth.graph_auth import get_auth_token
from ..libs.utils.config.config import settings
from ..libs.utils.db.mongodb.mongo import mongo_manager, get_db
from ..libs.utils.db.mongodb.repositories import ProjectRepository
from ..libs.utils.db.mongodb.schemas.schemas import AnalysisRequest, ProjectTag, StandupMeetingConfig, ProjectCreate, ProjectUpdate
from ..libs.services.fastapi.analytics import AnalyticsService
from ..libs.services.fastapi.graph_service import GraphService
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Connects to the database on startup and disconnects on shutdown.
    """
    logger.info("Application startup...")
    mongo_manager.connect()
    db = mongo_manager.db
    project_repo = ProjectRepository(db)
    project_repo.create_indexes()
    yield
    logger.info("Application shutdown...")
    mongo_manager.disconnect()


app = FastAPI(
    title="Standup Performance Analytics",
    description="An API to analyze standup meeting attendance from MS Teams.",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/projects/active",
         response_model=List[ProjectTag],
         summary="Get Active Projects",
         description="Fetches a list of all project tags that are marked as active in the database.")
def get_active_projects(db: Database = Depends(get_db)):
    """
    Endpoint to retrieve all active project configurations.
    This is used by the frontend to populate the project selection dropdown.
    """
    repo = ProjectRepository(db)
    projects = repo.get_all_active_projects()
    if not projects:
        logger.warning("No active projects found in the database.")
    return projects

@app.get("/projects",
            response_model=List[StandupMeetingConfig],
            summary="Get All Projects",
            description="Fetches a list of all project configurations from the database.")
def get_all_projects(db: Database = Depends(get_db)):
    """
    Endpoint to retrieve all project configurations.
    """
    repo = ProjectRepository(db)
    return repo.get_all_projects()


@app.post("/projects",
            response_model=StandupMeetingConfig,
            summary="Create a new project",
            description="Adds a new project configuration to the database.")
def create_project(project: ProjectCreate, db: Database = Depends(get_db)):
    repo = ProjectRepository(db)
    db_project = repo.get_project_by_tag(project.project_tag)
    if db_project:
        raise HTTPException(status_code=400, detail="Project tag already exists.")
    
    new_project = repo.create_project(project)
    if not new_project:
        raise HTTPException(status_code=500, detail="Failed to create project.")
    return new_project


@app.put("/projects/{project_tag}",
            response_model=StandupMeetingConfig,
            summary="Update a project",
            description="Updates an existing project configuration.")
def update_project(project_tag: str, project_update: ProjectUpdate, db: Database = Depends(get_db)):
    repo = ProjectRepository(db)
    updated_project = repo.update_project(project_tag, project_update)
    if not updated_project:
        raise HTTPException(status_code=404, detail=f"Project with tag '{project_tag}' not found.")
    return updated_project


@app.delete("/projects/{project_tag}",
            summary="Delete a project",
            description="Deletes a project configuration from the database.")
def delete_project(project_tag: str, db: Database = Depends(get_db)):
    repo = ProjectRepository(db)
    if not repo.delete_project(project_tag):
        raise HTTPException(status_code=404, detail=f"Project with tag '{project_tag}' not found.")
    return {"message": f"Project '{project_tag}' deleted successfully."}


@app.post("/analyze",
          summary="Analyze Standup Performance",
          description="Performs attendance and punctuality analysis for a given project and date range.")
def analyze_standup(
        req: AnalysisRequest,
        db: Database = Depends(get_db),
        token: str = Depends(get_auth_token)
):
    """
    This endpoint is the core of the analytics function.
    - It uses a project tag to look up the meeting configuration.
    - It uses OAuth2 to get a token for the Graph API.
    - It will then (in the next steps) call services to perform the analysis.
    """
    logger.info(f"Received analysis request for project: {req.project_tag}")
    repo = ProjectRepository(db)

    project_config = repo.get_project_by_tag(req.project_tag)
    if not project_config:
        logger.error(f"Project tag '{req.project_tag}' not found or is inactive.")
        raise HTTPException(
            status_code=404,
            detail=f"Project configuration for tag '{req.project_tag}' not found."
        )

    graph_service = GraphService(token)
    analytics_service = AnalyticsService(graph_service)

    # 3. Perform the analysis
    analysis_result = analytics_service.analyze_project_performance(
        project_config=project_config,
        start_date_str=req.start_date,
        end_date_str=req.end_date
    )

    if "error" in analysis_result:
        raise HTTPException(
            status_code=404,
            detail=analysis_result["error"]
        )

    return analysis_result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.apps.fastapi.main:app", host=settings.HOST, port=settings.FASTAPI_PORT, reload=False, app_dir="backend/app")

