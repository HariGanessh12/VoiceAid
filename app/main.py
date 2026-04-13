import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
from app.routes import voice_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        logger.info(f"--> {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"<-- {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        return response

app = FastAPI(
    title="Nyaya Mitra 2.0 API",
    description="Backend for Voice-first AI Legal Assistant MVP",
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_webhook.router, tags=["webhook"])

@app.get("/")
async def serve_frontend():
    """Serves the root index.html frontend."""
    # We load from the repository root since main.py is inside app/
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"Error loading index.html: {e}", status_code=500)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "nyaya-mitra-app"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
