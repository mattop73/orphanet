# Bayesian Disease Diagnosis API

A FastAPI-based application for rare disease diagnosis using Bayesian inference on Orphanet clinical data.

## Features

- **Bayesian Inference**: Calculates disease probabilities based on present and absent symptoms
- **Comprehensive Database**: Uses Orphanet rare disease clinical signs and symptoms data
- **RESTful API**: Full REST API with automatic OpenAPI documentation
- **Multiple Deployment Options**: Docker, Kubernetes, Railway, Render, Heroku support
- **Real-time Diagnosis**: Fast symptom-based disease probability calculations
- **Symptom Search**: Search and browse available symptoms and diseases

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Place your CSV file in the project directory
# clinical_signs_and_symptoms_in_rare_diseases.csv

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## API Endpoints

### Core Endpoints

- **GET /** - API information
- **GET /health** - Health check
- **GET /info** - System information and statistics
- **GET /docs** - Interactive API documentation
- **GET /redoc** - Alternative API documentation

### Data Endpoints

- **GET /symptoms** - List available symptoms with optional search
- **GET /diseases** - List available diseases with optional search

### Diagnosis Endpoint

- **POST /diagnose** - Perform Bayesian disease diagnosis

#### Request Format
```json
{
  "present_symptoms": ["Seizure", "Intellectual disability"],
  "absent_symptoms": ["Fever"],
  "top_n": 10
}
```

#### Response Format
```json
{
  "success": true,
  "results": [
    {
      "disorder_name": "Alexander disease",
      "orpha_code": "58",
      "probability": 0.045,
      "matching_symptoms": ["Seizure", "Intellectual disability"],
      "total_symptoms": 25,
      "confidence_score": 1.0
    }
  ],
  "total_diseases_evaluated": 1250,
  "input_symptoms": ["Seizure", "Intellectual disability"],
  "processing_time_ms": 45.2
}
```

### Data Management

- **POST /upload-data** - Upload new dataset CSV file

## Usage Examples

### Basic Diagnosis
```bash
curl -X POST "http://localhost:8000/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "present_symptoms": ["Seizure", "Intellectual disability"],
    "top_n": 5
  }'
```

### Advanced Diagnosis with Absent Symptoms
```bash
curl -X POST "http://localhost:8000/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "present_symptoms": ["Seizure", "Intellectual disability"],
    "absent_symptoms": ["Fever", "Rash"],
    "top_n": 10
  }'
```

### Search Symptoms
```bash
curl "http://localhost:8000/symptoms?search=seizure&limit=20"
```

### Get System Information
```bash
curl "http://localhost:8000/info"
```

## Bayesian Algorithm

The API uses a simplified Bayesian approach:

1. **Prior Probability**: Uniform distribution across all diseases
2. **Likelihood**: Based on symptom frequencies from Orphanet data
3. **Present Symptoms**: Multiply likelihood by symptom frequency
4. **Absent Symptoms**: Multiply likelihood by (1 - symptom frequency)
5. **Posterior**: Prior × Likelihood (normalized)

### Frequency Mapping
- Very frequent (99-80%): 0.9
- Frequent (79-30%): 0.55
- Occasional (29-5%): 0.17
- Very rare (<5%): 0.025
- Unknown frequency: 0.5

## Cloud Deployment Options

### 1. Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 2. Render
- Connect your GitHub repository
- Choose "Web Service"
- Use Python environment
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name
git push heroku main
```

### 4. Kubernetes
```bash
# Apply the configuration
kubectl apply -f kubernetes.yaml
```

## Environment Variables

- `API_HOST`: Host to bind to (default: 0.0.0.0)
- `API_PORT`: Port to bind to (default: 8000)
- `API_WORKERS`: Number of worker processes (default: 1)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)

## Data Format

The API expects a CSV file with the following columns:
- `disorder_id`: Unique disorder identifier
- `orpha_code`: Orphanet disorder code
- `disorder_name`: Disease name
- `disorder_type`: Type of disorder
- `hpo_id`: HPO term identifier
- `hpo_term`: Human Phenotype Ontology term (symptom)
- `hpo_frequency`: Frequency of symptom in disease
- `diagnostic_criteria`: Diagnostic criteria (optional)

## Health Monitoring

- **Health Check**: `GET /health`
- **System Info**: `GET /info`
- **Metrics**: Processing time included in diagnosis responses

## Error Handling

The API provides detailed error responses:
- 400: Bad Request (invalid symptoms, malformed request)
- 503: Service Unavailable (data not loaded)
- 500: Internal Server Error (processing failures)

## Performance

- **Typical Response Time**: 50-200ms for diagnosis
- **Memory Usage**: ~500MB with full dataset loaded
- **Concurrent Requests**: Supports multiple simultaneous diagnoses

## Security Considerations

- Input validation for all endpoints
- Rate limiting recommended for production
- CORS configuration required for web applications
- Consider authentication for data upload endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project uses Orphanet data which is freely available for research and educational purposes.

## Support

For issues and questions:
- Check the `/docs` endpoint for API documentation
- Review logs for debugging information
- Ensure CSV data format matches requirements