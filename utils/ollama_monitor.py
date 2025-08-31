import psutil
import subprocess
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
import threading
from collections import deque

logger = logging.getLogger("Ollama-Monitor")

@dataclass
class OllamaMetrics:
    """Data class for Ollama metrics"""
    timestamp: datetime
    status: str  # running, stopped, error
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_mb: float
    active_models: List[str]
    total_requests: int
    error_count: int
    response_time_avg: float
    model_usage: Dict[str, int]  # model_name -> usage_count

class OllamaMonitor:
    """Monitor Ollama service status and performance"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.metrics_history = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_metrics = None
        self.error_count = 0
        self.total_requests = 0
        self.response_times = deque(maxlen=100)
        self.model_usage = {}
        
    def start_monitoring(self, interval: int = 10):
        """Start Ollama monitoring in background thread"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Ollama monitoring started")
        
    def stop_monitoring(self):
        """Stop Ollama monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Ollama monitoring stopped")
        
    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                metrics = self._collect_ollama_metrics()
                self.metrics_history.append(metrics)
                self.last_metrics = metrics
                
                # Log significant events
                if metrics.status == "error":
                    logger.error(f"Ollama service error detected: {metrics}")
                elif metrics.cpu_percent > 80:
                    logger.warning(f"High Ollama CPU usage: {metrics.cpu_percent}%")
                elif metrics.memory_percent > 80:
                    logger.warning(f"High Ollama memory usage: {metrics.memory_percent}%")
                    
            except Exception as e:
                logger.error(f"Error in Ollama monitoring: {e}")
                self.error_count += 1
                
            time.sleep(interval)
    
    def _collect_ollama_metrics(self) -> OllamaMetrics:
        """Collect current Ollama metrics"""
        try:
            # Check if Ollama process is running
            ollama_process = self._find_ollama_process()
            
            if not ollama_process:
                return OllamaMetrics(
                    timestamp=datetime.utcnow(),
                    status="stopped",
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    memory_used_mb=0.0,
                    disk_usage_mb=0.0,
                    active_models=[],
                    total_requests=self.total_requests,
                    error_count=self.error_count,
                    response_time_avg=0.0,
                    model_usage=self.model_usage.copy()
                )
            
            # Get process metrics
            cpu_percent = ollama_process.cpu_percent()
            memory_info = ollama_process.memory_info()
            memory_percent = ollama_process.memory_percent()
            
            # Get disk usage for Ollama models
            disk_usage = self._get_ollama_disk_usage()
            
            # Get active models
            active_models = self._get_active_models()
            
            # Calculate average response time
            response_time_avg = sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
            
            # Check service health
            status = "running" if self._check_ollama_health() else "error"
            
            return OllamaMetrics(
                timestamp=datetime.utcnow(),
                status=status,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_info.rss / (1024 * 1024),
                disk_usage_mb=disk_usage,
                active_models=active_models,
                total_requests=self.total_requests,
                error_count=self.error_count,
                response_time_avg=response_time_avg,
                model_usage=self.model_usage.copy()
            )
            
        except Exception as e:
            logger.error(f"Error collecting Ollama metrics: {e}")
            return OllamaMetrics(
                timestamp=datetime.utcnow(),
                status="error",
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_mb=0.0,
                active_models=[],
                total_requests=self.total_requests,
                error_count=self.error_count + 1,
                response_time_avg=0.0,
                model_usage=self.model_usage.copy()
            )
    
    def _find_ollama_process(self) -> Optional[psutil.Process]:
        """Find the Ollama process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                    return proc
                elif proc.info['cmdline'] and any('ollama' in cmd.lower() for cmd in proc.info['cmdline']):
                    return proc
        except Exception as e:
            logger.error(f"Error finding Ollama process: {e}")
        return None
    
    def _get_ollama_disk_usage(self) -> float:
        """Get disk usage for Ollama models directory"""
        try:
            # Common Ollama model directories
            ollama_dirs = [
                "~/.ollama/models",
                "/usr/local/share/ollama/models",
                "/opt/ollama/models"
            ]
            
            import os
            for dir_path in ollama_dirs:
                expanded_path = os.path.expanduser(dir_path)
                if os.path.exists(expanded_path):
                    total_size = 0
                    for dirpath, dirnames, filenames in os.walk(expanded_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                total_size += os.path.getsize(filepath)
                            except OSError:
                                continue
                    return total_size / (1024 * 1024)  # Convert to MB
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating Ollama disk usage: {e}")
            return 0.0
    
    def _get_active_models(self) -> List[str]:
        """Get list of active Ollama models"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.debug(f"Error getting active models: {e}")
        return []
    
    def _check_ollama_health(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def record_request(self, model: str, response_time: float, success: bool = True):
        """Record a request to Ollama"""
        self.total_requests += 1
        self.response_times.append(response_time)
        
        if model not in self.model_usage:
            self.model_usage[model] = 0
        self.model_usage[model] += 1
        
        if not success:
            self.error_count += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of Ollama metrics"""
        if not self.metrics_history:
            return {
                "status": "no_data",
                "message": "No metrics collected yet"
            }
        
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 measurements
        
        return {
            "current_status": self.last_metrics.status if self.last_metrics else "unknown",
            "uptime": self._calculate_uptime(),
            "performance": {
                "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                "avg_memory_percent": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                "avg_memory_used_mb": sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics),
                "avg_response_time": sum(m.response_time_avg for m in recent_metrics) / len(recent_metrics),
            },
            "usage": {
                "total_requests": self.total_requests,
                "error_count": self.error_count,
                "success_rate": (self.total_requests - self.error_count) / max(self.total_requests, 1),
                "model_usage": self.model_usage,
                "active_models": self.last_metrics.active_models if self.last_metrics else []
            },
            "system": {
                "disk_usage_mb": self.last_metrics.disk_usage_mb if self.last_metrics else 0.0,
                "process_count": len([m for m in recent_metrics if m.status == "running"])
            },
            "recent_metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "status": m.status,
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "response_time_avg": m.response_time_avg
                }
                for m in recent_metrics
            ]
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate Ollama service uptime"""
        if not self.metrics_history:
            return "unknown"
        
        running_metrics = [m for m in self.metrics_history if m.status == "running"]
        if not running_metrics:
            return "stopped"
        
        first_running = running_metrics[0].timestamp
        uptime_seconds = (datetime.utcnow() - first_running).total_seconds()
        
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        if not self.last_metrics:
            return {"status": "no_data"}
        
        return {
            "timestamp": self.last_metrics.timestamp.isoformat(),
            "status": self.last_metrics.status,
            "cpu_percent": self.last_metrics.cpu_percent,
            "memory_percent": self.last_metrics.memory_percent,
            "memory_used_mb": self.last_metrics.memory_used_mb,
            "disk_usage_mb": self.last_metrics.disk_usage_mb,
            "active_models": self.last_metrics.active_models,
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "response_time_avg": self.last_metrics.response_time_avg,
            "model_usage": self.model_usage
        }

# Global Ollama monitor instance
ollama_monitor = OllamaMonitor()

# Convenience functions
def start_ollama_monitoring(interval: int = 10):
    """Start Ollama monitoring"""
    ollama_monitor.start_monitoring(interval)

def stop_ollama_monitoring():
    """Stop Ollama monitoring"""
    ollama_monitor.stop_monitoring()

def get_ollama_metrics():
    """Get Ollama metrics summary"""
    return ollama_monitor.get_metrics_summary()

def get_ollama_realtime():
    """Get real-time Ollama metrics"""
    return ollama_monitor.get_realtime_metrics()

def record_ollama_request(model: str, response_time: float, success: bool = True):
    """Record an Ollama request"""
    ollama_monitor.record_request(model, response_time, success)
