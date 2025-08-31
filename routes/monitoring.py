from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import psutil
import os
import time
from datetime import datetime, timedelta
import json

from utils.monitoring import get_application_health, monitor
from utils.ollama_monitor import get_ollama_metrics, get_ollama_realtime, start_ollama_monitoring
from database import get_collection
from config import config

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Check database connection
        collection = get_collection()
        collection.count()
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        
        # Determine health status
        status = "healthy"
        if cpu_percent > 90 or memory_percent > 90 or disk_usage > 90:
            status = "degraded"
        if cpu_percent > 95 or memory_percent > 95 or disk_usage > 95:
            status = "unhealthy"
            
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "healthy",
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory_percent:.1f}%",
                "disk_usage": f"{disk_usage:.1f}%"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with full application status"""
    return get_application_health()

@router.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    try:
        metrics = monitor.metrics_collector.get_metrics_summary()
        
        # Add system information
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "platform": psutil.sys.platform
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "system_info": system_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance metrics only"""
    try:
        metrics = monitor.metrics_collector.get_metrics_summary()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": metrics["performance"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")

@router.get("/metrics/system")
async def get_system_metrics():
    """Get system metrics only"""
    try:
        metrics = monitor.metrics_collector.get_metrics_summary()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": metrics["system"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving system metrics: {str(e)}")

@router.get("/status")
async def get_application_status():
    """Get comprehensive application status"""
    try:
        # Get basic health
        health = get_application_health()
        
        # Get system metrics
        system_metrics = monitor.metrics_collector.get_metrics_summary()
        
        # Get database info
        collection = get_collection()
        doc_count = collection.count()
        
        # Get recent operations
        recent_operations = list(monitor.metrics_collector.performance_metrics)[-5:]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": "RAG Application",
                "version": "1.0.0",
                "uptime_seconds": health["uptime_seconds"],
                "start_time": health["start_time"],
                "status": health["status"]
            },
            "database": {
                "document_count": doc_count,
                "status": "connected"
            },
            "performance": {
                "success_rate": system_metrics["performance"]["success_rate"],
                "avg_duration": system_metrics["performance"]["avg_duration"],
                "total_operations": system_metrics["performance"]["total_operations"]
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent
            },
            "recent_operations": [
                {
                    "operation": op.operation,
                    "duration": op.duration,
                    "success": op.success,
                    "timestamp": op.timestamp.isoformat()
                }
                for op in recent_operations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving application status: {str(e)}")

@router.get("/logs/recent")
async def get_recent_logs(limit: int = 50):
    """Get recent application logs"""
    try:
        log_file = "logs/app.log"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "No log file found"}
        
        logs = []
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    log_entry = json.loads(line.strip())
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    # Handle non-JSON lines
                    logs.append({"raw": line.strip()})
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "log_count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@router.get("/logs/errors")
async def get_error_logs(limit: int = 20):
    """Get recent error logs only"""
    try:
        log_file = "logs/app.log"
        if not os.path.exists(log_file):
            return {"errors": [], "message": "No log file found"}
        
        errors = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry.get("level") == "ERROR":
                        errors.append(log_entry)
                        if len(errors) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error_count": len(errors),
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving error logs: {str(e)}")

@router.get("/config")
async def get_configuration():
    """Get application configuration (non-sensitive)"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "configuration": {
            "embedding_model": config.EMBEDDING_MODEL,
            "llm_model": config.LLM_MODEL,
            "max_tokens": config.MAX_TOKENS,
            "temperature": config.TEMPERATURE,
            "chromadb_path": config.CHROMADB_PATH
        }
    }

@router.get("/endpoints")
async def get_endpoint_stats():
    """Get endpoint usage statistics"""
    try:
        request_counts = monitor.metrics_collector.request_counts
        error_counts = monitor.metrics_collector.error_counts
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "request_counts": dict(request_counts),
                "error_counts": dict(error_counts)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving endpoint stats: {str(e)}")

@router.get("/ollama/status")
async def get_ollama_status():
    """Get Ollama service status and metrics"""
    try:
        return get_ollama_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Ollama status: {str(e)}")

@router.get("/ollama/realtime")
async def get_ollama_realtime_status():
    """Get real-time Ollama metrics"""
    try:
        return get_ollama_realtime()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Ollama realtime metrics: {str(e)}")

@router.post("/ollama/start-monitoring")
async def start_ollama_monitoring_endpoint():
    """Start Ollama monitoring"""
    try:
        start_ollama_monitoring()
        return {"message": "Ollama monitoring started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting Ollama monitoring: {str(e)}")
