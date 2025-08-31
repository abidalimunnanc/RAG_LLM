from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from routes import documents, search, rag_routes, upload, health, monitoring
from database import startup_event
from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
import sys

# Import monitoring system
from utils.monitoring import monitor
from utils.middleware import MonitoringMiddleware, SecurityMiddleware, RateLimitingMiddleware
from utils.ollama_monitor import start_ollama_monitoring

# Configure logging
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Log file (rotating, keeps logs clean)
log_file = "app.log"
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler (so you still see logs in terminal)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Root logger setup
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    
    # Start monitoring system
    monitor.start_monitoring()
    
    # Start Ollama monitoring
    start_ollama_monitoring(interval=10)  # Monitor every 10 seconds
    logging.info("Application started with monitoring enabled")
    
    yield
    
    # Shutdown
    monitor.stop_monitoring()
    logging.info("Application shutdown complete")

app = FastAPI(
    title="RAG Application API",
    description="Retrieval-Augmented Generation with Vector Search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add monitoring and security middleware
app.add_middleware(MonitoringMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=200)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(rag_routes.router, prefix="/rag", tags=["RAG"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def read_frontend():
    with open("frontend.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Serve monitoring dashboard
@app.get("/monitoring-dashboard", response_class=HTMLResponse)
async def read_monitoring_dashboard():
    with open("monitoring_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# Serve Ollama monitoring dashboard
@app.get("/ollama-dashboard", response_class=HTMLResponse)
async def read_ollama_dashboard():
    with open("ollama_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
