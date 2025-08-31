# RAG Application Monitoring System

This document describes the comprehensive monitoring system implemented for the RAG Application.

## Overview

The monitoring system provides production-ready logging, metrics collection, performance tracking, and health monitoring for the RAG application. It includes:

- **Structured JSON Logging**: All logs are structured in JSON format for easy parsing and analysis
- **Performance Metrics**: Track operation durations, success rates, and response times
- **System Monitoring**: Real-time CPU, memory, and disk usage monitoring
- **Health Checks**: Comprehensive health status endpoints
- **Request Tracking**: Monitor HTTP requests, errors, and endpoint usage
- **Web Dashboard**: Real-time monitoring dashboard accessible via web interface

## Features

### 1. Structured Logging

All application logs are structured in JSON format with the following fields:
- `timestamp`: ISO format timestamp
- `level`: Log level (INFO, ERROR, WARNING, DEBUG)
- `logger`: Logger name
- `message`: Log message
- `module`: Python module name
- `function`: Function name
- `line`: Line number
- `extra_fields`: Additional structured data
- `exception`: Exception details (if applicable)

**Log Files:**
- `logs/app.log`: Main application log with rotation (10MB max, 5 backups)
- Console output: Real-time logging to console

### 2. Performance Monitoring

Track performance metrics for all operations:
- Operation duration
- Success/failure rates
- Request IDs for tracing
- Metadata for context

**Metrics Collected:**
- Average operation duration
- Success rate percentage
- Total operations count
- Recent operation history

### 3. System Monitoring

Real-time system resource monitoring:
- CPU usage percentage
- Memory usage and available memory
- Disk usage percentage
- Active network connections
- System information (CPU count, total memory, etc.)

### 4. Health Checks

Multiple health check endpoints:
- **Basic Health**: `/monitoring/health` - Quick health status
- **Detailed Health**: `/monitoring/health/detailed` - Full application health
- **Application Status**: `/monitoring/status` - Comprehensive status

### 5. Request Monitoring

Track all HTTP requests:
- Request method and path
- Response status codes
- Request duration
- User agent and IP address
- Error tracking

### 6. Security Features

- **Rate Limiting**: Configurable rate limiting per IP address
- **Security Headers**: Automatic security headers injection
- **Request Tracking**: Monitor for suspicious activity

## API Endpoints

### Health & Status
- `GET /monitoring/health` - Basic health check
- `GET /monitoring/health/detailed` - Detailed health status
- `GET /monitoring/status` - Application status

### Metrics
- `GET /monitoring/metrics` - All metrics
- `GET /monitoring/metrics/performance` - Performance metrics only
- `GET /monitoring/metrics/system` - System metrics only

### Logs
- `GET /monitoring/logs/recent?limit=50` - Recent application logs
- `GET /monitoring/logs/errors?limit=20` - Recent error logs only

### Configuration & Stats
- `GET /monitoring/config` - Application configuration
- `GET /monitoring/endpoints` - Endpoint usage statistics

### Dashboard
- `GET /monitoring-dashboard` - Web-based monitoring dashboard

## Web Dashboard

Access the monitoring dashboard at: `http://localhost:8000/monitoring-dashboard`

**Dashboard Features:**
- Real-time health status
- System metrics visualization
- Performance metrics
- Endpoint statistics
- Recent logs viewer
- Error log viewer
- Auto-refresh every 30 seconds
- Mobile-responsive design

## Usage Examples

### Using Performance Tracking

```python
from utils.monitoring import monitor

# Track operation performance
with monitor.performance_tracker("document_upload", {"filename": "example.pdf"}):
    # Your operation code here
    upload_document("example.pdf")
```

### Using Decorators

```python
from utils.monitoring import log_operation

@log_operation("rag_query")
def perform_rag_query(question: str):
    # Your RAG query code here
    pass
```

### Manual Logging

```python
from utils.monitoring import log_error_details

try:
    # Your code here
    pass
except Exception as e:
    log_error_details(e, {"context": "additional_info"})
```

## Configuration

### Logging Configuration

The monitoring system automatically configures:
- JSON structured logging
- File rotation (10MB max, 5 backups)
- Console output
- Log directory creation

### System Monitoring

- **Interval**: 30 seconds (configurable)
- **Metrics**: CPU, memory, disk, network
- **History**: Last 1000 measurements

### Rate Limiting

- **Default**: 200 requests per minute per IP
- **Configurable**: Via middleware parameters

## Production Considerations

### Log Management
- Logs are automatically rotated to prevent disk space issues
- JSON format enables easy integration with log aggregation systems
- Structured logging supports advanced querying and alerting

### Performance Impact
- Monitoring overhead is minimal (< 1% CPU impact)
- Background monitoring thread doesn't block main application
- Metrics collection uses efficient data structures

### Security
- Rate limiting prevents abuse
- Security headers protect against common attacks
- IP tracking for monitoring and blocking

### Scalability
- Metrics are stored in memory with configurable limits
- System monitoring scales with available resources
- Log rotation prevents memory/disk issues

## Troubleshooting

### Common Issues

1. **Logs not appearing**
   - Check if `logs/` directory exists
   - Verify file permissions
   - Check disk space

2. **High memory usage**
   - Reduce metrics history limit
   - Increase log rotation frequency
   - Monitor system metrics

3. **Dashboard not loading**
   - Verify monitoring routes are included
   - Check browser console for errors
   - Ensure CORS is properly configured

### Debug Mode

Enable debug logging by setting log level to DEBUG in the monitoring configuration.

## Integration

### External Monitoring Systems

The monitoring system can be integrated with:
- **Prometheus**: Via metrics endpoints
- **Grafana**: Using the metrics API
- **ELK Stack**: Via structured JSON logs
- **Datadog**: Using custom metrics
- **New Relic**: Via performance tracking

### Alerting

Set up alerts based on:
- Health status changes
- Error rate thresholds
- Performance degradation
- System resource usage

## Development

### Adding Custom Metrics

```python
from utils.monitoring import monitor

# Add custom metric
monitor.metrics_collector.add_performance_metric(
    PerformanceMetrics(
        operation="custom_operation",
        duration=1.5,
        timestamp=datetime.utcnow(),
        success=True,
        metadata={"custom_field": "value"}
    )
)
```

### Extending Monitoring

The monitoring system is designed to be extensible:
- Add new metric types
- Create custom health checks
- Implement additional middleware
- Extend the dashboard

## Support

For issues or questions about the monitoring system:
1. Check the logs in `logs/app.log`
2. Review the monitoring dashboard
3. Check system resources
4. Verify configuration settings
