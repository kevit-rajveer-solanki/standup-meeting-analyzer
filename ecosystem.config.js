module.exports = {
  apps: [
    {
      name: "standup-analyzer-backend-prod",
      script: "bash",
      args: "-c \".venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000\"",
      env: {
        // These values should be set in your deployment environment
        AZURE_CLIENT_ID: process.env.AZURE_CLIENT_ID,
        AZURE_CLIENT_SECRET: process.env.AZURE_CLIENT_SECRET,
        AZURE_TENANT_ID: process.env.AZURE_TENANT_ID,
        MONGO_URI: process.env.MONGO_URI || "mongodb://localhost:27017/",
        MONGO_DB_NAME: process.env.MONGO_DB_NAME || "standup_analytics",
        GRAPH_SCOPE: process.env.GRAPH_SCOPE || "https://graph.microsoft.com/.default",
      },
    },
    {
      name: "standup-analyzer-frontend-prod",
      script: "bash",
      args: "-c \".venv/bin/streamlit run frontend/app.py --server.headless=true\"",
      env: {
        STREAMLIT_SERVER_ADDRESS: "0.0.0.0",
        STREAMLIT_SERVER_PORT: "8501",
        // This should point to the address of your backend API
        BACKEND_API_URL: process.env.BACKEND_API_URL || "http://localhost:8000",
      },
    },
  ],
};
