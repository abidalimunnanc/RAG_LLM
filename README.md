# 🤖 RAG Application - AI Document Assistant

A powerful Retrieval-Augmented Generation (RAG) application built with FastAPI, ChromaDB, and Ollama for intelligent document processing and AI-powered question answering.

## 🚀 Features

### **Core Functionality**
- **📄 Document Upload**: Support for PDF, TXT, MD, and JSON files
- **🔍 Semantic Search**: Advanced vector-based document search
- **🧠 AI-Powered Q&A**: Intelligent question answering using Ollama
- **📊 Real-time Streaming**: Live AI response streaming
- **🎯 Context-Aware**: Uses relevant document context for accurate answers

### **Advanced Features**
- **📈 Comprehensive Monitoring**: Real-time system and Ollama monitoring
- **🔒 Security**: Rate limiting and security headers
- **📱 Modern UI**: Responsive web interface
- **⚡ Performance Optimized**: Efficient Ollama integration
- **🔄 Auto-refresh**: Real-time dashboard updates

### **Monitoring & Analytics**
- **📊 System Metrics**: CPU, memory, disk usage monitoring
- **🤖 Ollama Monitoring**: Model usage, response times, performance tracking
- **📝 Structured Logging**: JSON-formatted logs with rotation
- **🎯 Health Checks**: Comprehensive application health monitoring
- **📈 Performance Analytics**: Request/response time tracking

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Vector Database**: ChromaDB
- **AI Models**: Ollama (Local LLM)
- **Embeddings**: Sentence Transformers
- **Frontend**: HTML/CSS/JavaScript
- **Monitoring**: Custom monitoring system with real-time dashboards

## 📋 Prerequisites

- **Python 3.8+**
- **Ollama** installed and running
- **Git** for cloning the repository

### **Ollama Setup**
```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull gemma3:1b
ollama pull nomic-embed-text:v1.5
```

## 🚀 Quick Start

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd fastapi_rag_app
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Start the Application**
```bash
python -m uvicorn main:app --reload --port 8000
```

### **4. Access the Application**
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **System Monitoring**: http://localhost:8000/monitoring-dashboard
- **Ollama Monitoring**: http://localhost:8000/ollama-dashboard

## 📖 Usage Guide

### **1. Upload Documents**
1. Navigate to the main application
2. Drag and drop files or click "Choose Files"
3. Supported formats: PDF, TXT, MD, JSON
4. Documents are automatically processed and indexed

### **2. Search Documents**
1. Use the search section in the sidebar
2. Enter your search query
3. Adjust similarity threshold and result count
4. View relevant document snippets

### **3. Ask AI Questions**
1. Type your question in the main AI assistant section
2. The AI will use uploaded documents as context
3. Receive comprehensive, detailed answers
4. Watch real-time streaming responses

### **4. Monitor Performance**
1. Access monitoring dashboards from the sidebar
2. View real-time system metrics
3. Track Ollama performance and usage
4. Monitor application health

## 🔧 Configuration

### **Environment Variables**
Create a `.env` file for custom configuration:
```env
OLLAMA_HOST=http://localhost:11434
CHROMADB_PATH=./chromadb_storage
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gemma3:1b
MAX_TOKENS=2000
TEMPERATURE=0.7
```

### **Model Configuration**
Edit `config.py` to customize AI behavior:
```python
class Config:
    CHROMADB_PATH = "./chromadb_storage"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "gemma3:1b"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7
    MIN_RESPONSE_TOKENS = 50
    MAX_RESPONSE_TOKENS = 1500
```

## 📊 Monitoring & Analytics

### **System Monitoring Dashboard**
- **Health Status**: Application and service health
- **Performance Metrics**: Response times and success rates
- **System Resources**: CPU, memory, disk usage
- **Request Analytics**: Endpoint usage statistics

### **Ollama Monitoring Dashboard**
- **Model Status**: Active models and availability
- **Performance Tracking**: Response times and throughput
- **Resource Usage**: CPU and memory consumption
- **Request History**: Usage patterns and trends

### **API Endpoints**
```bash
# Health checks
GET /monitoring/health
GET /monitoring/health/detailed

# Metrics
GET /monitoring/metrics
GET /monitoring/metrics/performance
GET /monitoring/metrics/system

# Ollama monitoring
GET /monitoring/ollama/status
GET /monitoring/ollama/realtime

# Logs
GET /monitoring/logs/recent
GET /monitoring/logs/errors
```

## 🔒 Security Features

- **Rate Limiting**: 200 requests per minute per IP
- **Security Headers**: XSS protection, content type options
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error responses

## 📁 Project Structure

```
fastapi_rag_app/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── llm.py                 # Ollama integration and AI logic
├── rag.py                 # RAG pipeline implementation
├── database.py            # ChromaDB database operations
├── pdf_scraper.py         # PDF processing utilities
├── models.py              # Pydantic data models
├── requirements.txt       # Python dependencies
├── frontend.html          # Main web interface
├── monitoring_dashboard.html  # System monitoring dashboard
├── ollama_dashboard.html  # Ollama monitoring dashboard
├── routes/                # API route modules
│   ├── documents.py       # Document management routes
│   ├── search.py          # Search functionality routes
│   ├── rag_routes.py      # RAG processing routes
│   ├── upload.py          # File upload routes
│   ├── health.py          # Health check routes
│   └── monitoring.py      # Monitoring API routes
├── utils/                 # Utility modules
│   ├── logger.py          # Logging configuration
│   ├── monitoring.py      # Monitoring system
│   ├── middleware.py      # HTTP middleware
│   └── ollama_monitor.py  # Ollama monitoring
└── chromadb_storage/      # Vector database storage
```

## 🚀 Performance Optimization

### **Recent Improvements**
- **Eliminated infinite loops** in AI generation
- **Removed artificial delays** in streaming responses
- **Optimized token limits** for faster responses
- **Smart model management** with availability checking
- **Efficient retry logic** with controlled attempts

### **Performance Tips**
1. **Use appropriate models** for your use case
2. **Monitor resource usage** via dashboards
3. **Optimize document size** for faster processing
4. **Adjust token limits** based on response quality needs

## 🐛 Troubleshooting

### **Common Issues**

#### **Ollama Not Responding**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve
```

#### **Model Not Found**
```bash
# Pull the required model
ollama pull gemma3:1b

# Check available models
ollama list
```

#### **High Memory Usage**
- Monitor via Ollama dashboard
- Consider using smaller models
- Adjust token limits in config.py

#### **Slow Response Times**
- Check CPU usage in monitoring dashboard
- Verify Ollama service status
- Consider model optimization

### **Logs and Debugging**
- **Application logs**: `logs/app.log`
- **Monitoring data**: Available via API endpoints
- **Error tracking**: Built-in error monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local LLM capabilities
- **ChromaDB** for vector database functionality
- **FastAPI** for the web framework
- **Sentence Transformers** for embeddings

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the monitoring dashboards
3. Check application logs
4. Open an issue on GitHub

---

**Made with ❤️ for intelligent document processing and AI-powered insights**
