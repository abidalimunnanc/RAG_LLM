import logging
import time
import json
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import traceback
from contextlib import contextmanager
import hashlib
import uuid

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics"""
    operation: str
    duration: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SystemMetrics:
    """Data class for system metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    requests_per_minute: float

class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.performance_metrics: deque = deque(maxlen=max_history)
        self.system_metrics: deque = deque(maxlen=max_history)
        self.request_counts: defaultdict = defaultdict(int)
        self.error_counts: defaultdict = defaultdict(int)
        self.lock = threading.Lock()
        
    def add_performance_metric(self, metric: PerformanceMetrics):
        """Add a performance metric"""
        with self.lock:
            self.performance_metrics.append(metric)
            
    def add_system_metric(self, metric: SystemMetrics):
        """Add a system metric"""
        with self.lock:
            self.system_metrics.append(metric)
            
    def increment_request_count(self, endpoint: str):
        """Increment request count for an endpoint"""
        with self.lock:
            self.request_counts[endpoint] += 1
            
    def increment_error_count(self, error_type: str):
        """Increment error count for an error type"""
        with self.lock:
            self.error_counts[error_type] += 1
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        with self.lock:
            return {
                "performance": {
                    "total_operations": len(self.performance_metrics),
                    "avg_duration": self._calculate_avg_duration(),
                    "success_rate": self._calculate_success_rate(),
                    "recent_operations": list(self.performance_metrics)[-10:]
                },
                "system": {
                    "total_measurements": len(self.system_metrics),
                    "latest_metrics": list(self.system_metrics)[-1] if self.system_metrics else None,
                    "avg_cpu": self._calculate_avg_cpu(),
                    "avg_memory": self._calculate_avg_memory()
                },
                "requests": dict(self.request_counts),
                "errors": dict(self.error_counts)
            }
    
    def _calculate_avg_duration(self) -> float:
        """Calculate average operation duration"""
        if not self.performance_metrics:
            return 0.0
        return sum(m.duration for m in self.performance_metrics) / len(self.performance_metrics)
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate"""
        if not self.performance_metrics:
            return 0.0
        successful = sum(1 for m in self.performance_metrics if m.success)
        return successful / len(self.performance_metrics)
    
    def _calculate_avg_cpu(self) -> float:
        """Calculate average CPU usage"""
        if not self.system_metrics:
            return 0.0
        return sum(m.cpu_percent for m in self.system_metrics) / len(self.system_metrics)
    
    def _calculate_avg_memory(self) -> float:
        """Calculate average memory usage"""
        if not self.system_metrics:
            return 0.0
        return sum(m.memory_percent for m in self.system_metrics) / len(self.system_metrics)

class SystemMonitor:
    """Monitors system resources"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.monitoring_thread = None
        self.is_monitoring = False
        
    def start_monitoring(self, interval: int = 30):
        """Start system monitoring in background thread"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
            
    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                metric = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=psutil.cpu_percent(interval=1),
                    memory_percent=psutil.virtual_memory().percent,
                    memory_used_mb=psutil.virtual_memory().used / (1024 * 1024),
                    disk_usage_percent=psutil.disk_usage('/').percent,
                    active_connections=len(psutil.net_connections()),
                    requests_per_minute=0  # Will be calculated separately
                )
                self.metrics_collector.add_system_metric(metric)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")

class ApplicationMonitor:
    """Main application monitoring class"""
    
    def __init__(self, app_name: str = "RAG-Application"):
        self.app_name = app_name
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics_collector)
        self.start_time = datetime.utcnow()
        self.request_id_counter = 0
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup structured logging"""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            "logs/app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        console_handler.setLevel(logging.INFO)
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Create application logger
        self.logger = logging.getLogger(self.app_name)
        
    def start_monitoring(self):
        """Start all monitoring systems"""
        self.system_monitor.start_monitoring()
        self.logger.info("Application monitoring started", extra={
            "extra_fields": {
                "start_time": self.start_time.isoformat(),
                "app_name": self.app_name
            }
        })
        
    def stop_monitoring(self):
        """Stop all monitoring systems"""
        self.system_monitor.stop_monitoring()
        self.logger.info("Application monitoring stopped")
        
    @contextmanager
    def performance_tracker(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for tracking operation performance"""
        start_time = time.time()
        request_id = self._generate_request_id()
        
        try:
            self.logger.info(f"Starting operation: {operation}", extra={
                "extra_fields": {
                    "operation": operation,
                    "request_id": request_id,
                    "metadata": metadata or {}
                }
            })
            
            yield request_id
            
            duration = time.time() - start_time
            metric = PerformanceMetrics(
                operation=operation,
                duration=duration,
                timestamp=datetime.utcnow(),
                success=True,
                metadata=metadata
            )
            self.metrics_collector.add_performance_metric(metric)
            
            self.logger.info(f"Operation completed: {operation}", extra={
                "extra_fields": {
                    "operation": operation,
                    "request_id": request_id,
                    "duration": duration,
                    "success": True
                }
            })
            
        except Exception as e:
            duration = time.time() - start_time
            metric = PerformanceMetrics(
                operation=operation,
                duration=duration,
                timestamp=datetime.utcnow(),
                success=False,
                error_message=str(e),
                metadata=metadata
            )
            self.metrics_collector.add_performance_metric(metric)
            self.metrics_collector.increment_error_count(type(e).__name__)
            
            self.logger.error(f"Operation failed: {operation}", extra={
                "extra_fields": {
                    "operation": operation,
                    "request_id": request_id,
                    "duration": duration,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            })
            raise
            
    def log_request(self, method: str, path: str, status_code: int, duration: float, 
                   user_agent: str = None, ip_address: str = None):
        """Log HTTP request details"""
        self.metrics_collector.increment_request_count(f"{method} {path}")
        
        self.logger.info("HTTP Request", extra={
            "extra_fields": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration": duration,
                "user_agent": user_agent,
                "ip_address": ip_address
            }
        })
        
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log application errors"""
        self.metrics_collector.increment_error_count(type(error).__name__)
        
        self.logger.error("Application Error", extra={
            "extra_fields": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "context": context or {}
            }
        })
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status"""
        uptime = datetime.utcnow() - self.start_time
        metrics_summary = self.metrics_collector.get_metrics_summary()
        
        # Determine overall health
        health_status = "healthy"
        if metrics_summary["performance"]["success_rate"] < 0.95:
            health_status = "degraded"
        if metrics_summary["performance"]["success_rate"] < 0.8:
            health_status = "unhealthy"
            
        return {
            "status": health_status,
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "metrics": metrics_summary
        }
        
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        self.request_id_counter += 1
        return f"{self.app_name}-{int(time.time())}-{self.request_id_counter}"

# Global monitor instance
monitor = ApplicationMonitor()

# Convenience functions
def log_operation(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for logging operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with monitor.performance_tracker(operation, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def log_request_details(method: str, path: str, status_code: int, duration: float, 
                       user_agent: str = None, ip_address: str = None):
    """Log HTTP request details"""
    monitor.log_request(method, path, status_code, duration, user_agent, ip_address)

def log_error_details(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error details"""
    monitor.log_error(error, context)

def get_application_health() -> Dict[str, Any]:
    """Get application health status"""
    return monitor.get_health_status()
