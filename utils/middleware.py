import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import json
from .monitoring import log_request_details, log_error_details

logger = logging.getLogger("RAG-Application")

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring HTTP requests and responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        ip_address = self._get_client_ip(request)
        
        # Log request start
        logger.info(f"Request started: {method} {path}", extra={
            "extra_fields": {
                "method": method,
                "path": path,
                "user_agent": user_agent,
                "ip_address": ip_address,
                "query_params": dict(request.query_params)
            }
        })
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful request
            log_request_details(
                method=method,
                path=path,
                status_code=response.status_code,
                duration=duration,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Add custom headers
            response.headers["X-Request-Duration"] = str(duration)
            response.headers["X-Request-ID"] = f"{int(start_time)}-{hash(path)}"
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            log_error_details(e, {
                "method": method,
                "path": path,
                "duration": duration,
                "user_agent": user_agent,
                "ip_address": ip_address
            })
            
            # Re-raise the exception
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and basic protection"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting middleware"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_requests(current_time)
        
        # Check rate limit
        if not self._is_allowed(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content=json.dumps({"error": "Rate limit exceeded"}),
                status_code=429,
                media_type="application/json"
            )
        
        # Add request to tracking
        self._add_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, current_time: float):
        """Remove requests older than 1 minute"""
        cutoff_time = current_time - 60
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                req_time for req_time in self.request_counts[ip] 
                if req_time > cutoff_time
            ]
            if not self.request_counts[ip]:
                del self.request_counts[ip]
    
    def _is_allowed(self, client_ip: str, current_time: float) -> bool:
        """Check if request is allowed based on rate limit"""
        if client_ip not in self.request_counts:
            return True
        
        # Count requests in the last minute
        cutoff_time = current_time - 60
        recent_requests = sum(
            1 for req_time in self.request_counts[client_ip] 
            if req_time > cutoff_time
        )
        
        return recent_requests < self.requests_per_minute
    
    def _add_request(self, client_ip: str, current_time: float):
        """Add request to tracking"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append(current_time)
