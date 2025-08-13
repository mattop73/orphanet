#!/bin/bash

# Bayesian Diagnosis API Deployment Script

set -e

echo "🚀 Deploying Bayesian Diagnosis API..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if CSV file exists
if [ ! -f "file/clinical_signs_and_symptoms_in_rare_diseases.csv" ]; then
    echo "❌ CSV file 'file/clinical_signs_and_symptoms_in_rare_diseases.csv' not found!"
    echo "Please place your dataset file in the file/ directory."
    exit 1
fi

# Build and start the service
echo "📦 Building Docker image..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

# Wait for service to be ready
echo "⏳ Waiting for API to be ready..."
sleep 10

# Health check
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ API is running successfully!"
    echo ""
    echo "📊 API Endpoints:"
    echo "  • API Docs: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/health"
    echo "  • System Info: http://localhost:8000/info"
    echo "  • Diagnosis: POST http://localhost:8000/diagnose"
    echo ""
    echo "🧪 Test the API:"
    echo 'curl -X POST "http://localhost:8000/diagnose" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d "{\"present_symptoms\": [\"Seizure\", \"Intellectual disability\"], \"top_n\": 5}"'
else
    echo "❌ API failed to start. Check logs:"
    echo "docker-compose logs"
fi