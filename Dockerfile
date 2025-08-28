# Multi-stage build for Knowledge & Math Assistant

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy frontend source
COPY frontend/ ./

# Build the React app
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy RAG pipeline
COPY rag_pipeline/ ./rag_pipeline/

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Create directories for data persistence
RUN mkdir -p /app/data/chroma
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_PERSIST_DIRECTORY=/app/data/chroma
ENV LOG_LEVEL=INFO
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "backend.app:socket_app", "--host", "0.0.0.0", "--port", "8000"]