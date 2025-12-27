# Standup Performance Analytics

A web-based analytics tool to automatically track and visualize attendance and punctuality for recurring standup meetings using data from Microsoft Teams.

## Overview

This application provides project-based performance metrics by pulling attendance data directly from the Microsoft Graph API. It features a secure, backend-driven authentication flow and a clean, interactive web interface built with Streamlit for data visualization. The primary goal is to give managers and teams data-driven insights into their standup discipline without manual tracking.

## Key Features

- **Project-Based Reporting**: Analyze different meetings by configuring them as distinct "projects".
- **Secure Authentication**: Implements the OAuth2 Client Credentials flow on the backend. No tokens or secrets are exposed to the frontend.
- **Automated Metrics Calculation**:
  - **Attendance %**: Percentage of working-day meetings an individual attended.
  - **Punctuality %**: Percentage of attended meetings an individual joined on time (within 5 minutes).
  - **Average Meeting Duration**: The average length of standups in minutes.
  - **Average Attendees**: The average number of internal team members per meeting.
- **Intelligent Filtering**: Automatically excludes weekends and filters out external guests from the analysis.
- **Interactive Dashboard**:
  - High-level KPI cards for a quick overview.
  - "Top 5" and "Bottom 5" attendee tables to highlight trends.
  - A comprehensive "Full Team Report" with detailed statistics for every member.
- **User-Friendly Interface**: A simple, clean UI with tooltips on all metrics to explain how they are calculated.

## Architecture

The application follows a modern, decoupled architecture:

- **Backend**: A **FastAPI** application handles all business logic.
  - **Authentication**: **MSAL (Microsoft Authentication Library)** for Python is used for secure token acquisition.
  - **Database**: **MongoDB** stores project configurations (organizer email, meeting link), abstracting them away from the user.
  - **Data Source**: Fetches attendance data from the **Microsoft Graph API**.

- **Frontend**: A **Streamlit** application provides the user interface for selecting projects, setting date ranges, and viewing the analytics dashboard.

## Folder Structure

```
.
├── backend/
│   ├── app/
│   │   ├── auth/          # MS Graph API authentication
│   │   ├── db/            # MongoDB connection and repositories
│   │   ├── models/        # Pydantic data schemas
│   │   ├── services/      # Business logic and Graph API calls
│   │   ├── utils/         # Helper utilities
│   │   ├── config.py      # Environment variable management
│   │   └── main.py        # FastAPI application entrypoint
│   ├── .env             # (You create this) Environment variables
│   └── requirements.txt
│
├── frontend/
│   ├── app.py             # Streamlit application
│   └── requirements.txt
│
└── .venv/                 # Virtual environment
```

---

## Setup and Installation

Follow these steps to set up and run the project locally.

### Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- [MongoDB](https://www.mongodb.com/try/download/community) installed and running on its default port (`mongodb://localhost:27017`).
- An **Azure AD App Registration** with the required API permissions (`OnlineMeetingArtifact.Read.All`, `User.Read.All`) and credentials (Client ID, Client Secret, Tenant ID).

### Step 1: Clone the Repository

Clone this project to your local machine.

```shell
git clone <your-repository-url>
cd StandUPAnalyzer
```

### Step 2: Configure Environment Variables

Create a file named `.env` inside the `backend/` directory and populate it with your Azure and MongoDB details.

**File: `backend/.env`**
```ini
# Microsoft Graph API Credentials
AZURE_CLIENT_ID=<Your Azure App Client ID>
AZURE_CLIENT_SECRET=<Your Azure App Client Secret>
AZURE_TENANT_ID=<Your Azure Tenant ID>

# MongoDB Connection (default)
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=standup_analytics

# Microsoft Graph API Scope (default)
GRAPH_SCOPE=https://graph.microsoft.com/.default
```

### Step 3: Configure a Project in MongoDB

You must add a meeting configuration to the database.

1.  Connect to your MongoDB instance (e.g., using `mongosh`).
2.  Run the following command, replacing the values with your actual meeting details:

```javascript
db.getSiblingDB('standup_analytics').standup_meetings.insertOne({
  "project_tag": "DRVN101", // A unique name for your project
  "organizer_email": "your.organizer.email@yourcompany.com",
  "meeting_link": "https://teams.microsoft.com/l/meetup-join/", // The full meeting join link
  "is_active": true,
  "created_at": new Date(),
  "updated_at": new Date()
});
```

### Step 4: Install Dependencies

This project uses a shared virtual environment.

```shell
# From the project root directory (e.g., StandUPAnalyzer)
# Install backend packages
\ .\venv\Scripts\pip.exe install -r backend\requirements.txt

# Install frontend packages
\ .\venv\Scripts\pip.exe install -r frontend\requirements.txt
```

### Step 5: Run the Application

You will need **two separate terminals** running simultaneously.

**Terminal 1: Start the Backend**

In the project's root directory, run:
```shell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload
```
The API server will be running at `http://localhost:8000`.

**Terminal 2: Start the Frontend**

In the project's root directory, activate the virtual environment and run:
```shell
\ .\venv\Scripts\activate
streamlit run frontend/app.py
```
This will open the web interface in your browser.

## Usage

1.  Open the Streamlit URL in your browser.
2.  Select the desired `Project` from the sidebar dropdown.
3.  Choose the `Start Date` and `End Date` for your analysis.
4.  Click **Generate Report**.
5.  View the KPIs and analytics presented on the dashboard.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'app'`**: This typically means you are running the `uvicorn` command from the wrong directory. Ensure you are in the project's root folder (`StandUPAnalyzer`) and using the correct command specified in Step 5.
- **Connection Error on Frontend**: This means the backend server is not running or is not accessible at `http://localhost:8000`. Check your backend terminal for errors.
- **Error from backend: `... not found`**: This means the `organizer_email` or `meeting_link` in your MongoDB configuration is incorrect, or the application lacks the required Graph API permissions to access the data. Verify your MongoDB entry and Azure AD permissions.
