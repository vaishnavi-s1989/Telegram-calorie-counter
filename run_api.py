"""
Main entry point for running the FastAPI backend.

Local dev  : python run_api.py  (port 8000, reload=True)
IBM Code Engine: gunicorn is used directly via the Dockerfile CMD;
                 this file is not used in production.
"""
import uvicorn
from config import config
from src.api.main import app

if __name__ == '__main__':
    port   = int(config.PORT) if config.APP_ENV == "production" else 8000
    reload = config.DEBUG

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="debug" if config.DEBUG else "info",
    )

# Made with Bob
