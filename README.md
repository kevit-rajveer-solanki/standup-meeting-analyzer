# Standup Performance Analytics

A web-based analytics tool to automatically track and visualize attendance and punctuality for recurring standup meetings using data from Microsoft Teams.

## Overview

This application provides project-based performance metrics by pulling attendance data directly from the Microsoft Graph API. It features a secure, backend-driven authentication flow and a clean, interactive web interface built with Streamlit for data visualization. The primary goal is to give managers and teams data-driven insights into their standup discipline without manual tracking.

## Key Features

- **Project-Based Reporting**: Analyze different meetings by configuring them as distinct "projects".
- **Project Management UI**: A built-in dashboard to easily add, edit, and delete project configurations without direct database access.
- **Secure Authentication**: Implements the OAuth2 Client Credentials flow on the backend. No tokens or secrets are exposed to the frontend.
- **Automated Metrics Calculation**:
  - **Attendance %**: Percentage of working-day meetings an individual attended.
  - **Punctuality %**: Percentage of attended meetings an individual joined on time (within 5 minutes).
  - **Average Meeting Duration**: The average length of standups in minutes.
  - **Average Attendees**: The average number of internal team members per meeting.
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
│   ├── auth/          # MS Graph API authentication
│   ├── db/            # MongoDB connection and repositories
│   ├── models/        # Pydantic data schemas
│   ├── services/      # Business logic and Graph API calls
│   ├── utils/         # Helper utilities
│   ├── config.py      # Environment variable management
│   └── main.py        # FastAPI application entrypoint
│   
│
├── frontend/
│   ├── app.py             # Streamlit application
│   
│
├── .env                   # (You create this) Environment variables
├── example.env            # Example environment file
└── ...
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
cd standup-meeting-analyzer
```

### Step 2: Create and Activate Virtual Environment

Create and activate a virtual environment to manage project dependencies.

**On Windows:**
```shell
python -m venv venv
.\venv\Scripts\activate
```

**On Linux/macOS:**
```shell
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Install the required packages for both the frontend and backend.

```shell
# From the project root directory
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the **project root directory**. You can do this by copying the provided example file.

**On Windows:**
```shell
copy example.env .env
```

**On Linux/macOS:**
```shell
cp example.env .env
```

Now, open the `.env` file and populate it with your Azure and MongoDB details.

**File: `.env`**
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

### Step 5: Run the Application

You will need **two separate terminals** running simultaneously. Ensure your virtual environment is activated in both.

**Terminal 1: Start the Backend**

In the project's root directory, run:
```shell
python -m uvicorn backend.apps.fastapi.main:app --host 0.0.0.0 --port 8000 --reload
```
The API server will be running at `http://localhost:8000`.

**Terminal 2: Start the Frontend**

In the project's root directory, run:
```shell
streamlit run frontend/app.py
```
This will open the web interface in your browser.

## Usage

### Generating a Report

1.  Open the Streamlit URL in your browser.
2.  The application will open on the **Analytics** tab.
3.  In the sidebar, select the desired `Project` from the dropdown.
4.  Choose the `Start Date` and `End Date` for your analysis.
5.  Click **Generate Report**.
6.  View the KPIs and analytics presented on the dashboard.

### Managing Projects

The application now includes a UI for managing projects, so you no longer need to add them to the database manually.

1.  Navigate to the **Manage Projects** tab.
2.  **To add a new project**: Fill in the "Add New Project" form and click "Add Project".
3.  **To edit or delete a project**: Find the project in the "Existing Projects" list, expand it, and click "Edit" or "Delete".

## Troubleshooting

- **`ModuleNotFoundError`**: This typically means you are running a command from the wrong directory or your virtual environment is not activated. Ensure you are in the project's root folder and the `(venv)` indicator is visible in your terminal prompt.
- **Connection Error on Frontend**: This means the backend server is not running or is not accessible at `http://localhost:8000`. Check your backend terminal for errors.
- **Error from backend: `... not found`**: This can mean the `organizer_email` or `meeting_link` for a project is incorrect, or the application lacks the required Graph API permissions. Use the "Manage Projects" UI to correct the details, or verify your Azure AD permissions.
- **`ValidationError` on Startup**: This error means the backend failed to load the required environment variables from the `.env` file. Ensure your `.env` file is in the project root, is named correctly, and contains all the required fields.
