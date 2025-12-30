module.exports = {
  apps: [
    // ================= Backend : FastAPI =================
    {
      name: "standup-analyzer-backend-prod",

      // 🔥 IMPORTANT: run as module, not as file
      script: "python3.12",
      args: "-m backend.apps.fastapi.main",

      env: {
        PYTHONPATH: process.env.PYTHONPATH + ":" + process.cwd(),

        // Azure / Microsoft Graph
        AZURE_CLIENT_ID: process.env.AZURE_CLIENT_ID,
        AZURE_CLIENT_SECRET: process.env.AZURE_CLIENT_SECRET,
        AZURE_TENANT_ID: process.env.AZURE_TENANT_ID,
        GRAPH_SCOPE:
          process.env.GRAPH_SCOPE ||
          "https://graph.microsoft.com/.default",

        // MongoDB
        MONGO_URI: process.env.MONGO_URI || "mongodb://localhost:27017/",
        MONGO_DB_NAME: process.env.MONGO_DB_NAME || "standup_analytics",

        ENV: "production",
      },
    },

    // ================= Frontend : Streamlit =================
    {
      name: "standup-analyzer-frontend-prod",
      script: "bash",
      args:
        "-c \"streamlit run frontend/app.py --server.headless=true\"",
      env: {
        PYTHONPATH: process.env.PYTHONPATH + ":" + process.cwd(),

        STREAMLIT_SERVER_ADDRESS: "0.0.0.0",
        STREAMLIT_SERVER_PORT: "8501",

        // Must match Streamlit code
        BACKEND_API_URL:
          process.env.BACKEND_API_URL ||
          "http://localhost:8000",

        ENV: "production",
      },
    },
  ],
};
