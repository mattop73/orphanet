# 🧬 Bayesian Disease Diagnosis - Usage Guide

## Quick Start

### 1. Start the Web Interface
```bash
python3 start_interface.py
```
This will:
- Start the API server on `http://localhost:8000`
- Automatically open the web interface in your browser
- Load all 114,961 disease-symptom associations

### 2. Using the Web Interface

#### Step 1: Select Symptoms
- **Search Box**: Type to search through 8,595 available symptoms
- **Toggle Buttons**: Switch between "Present Symptoms" and "Absent Symptoms"
- **Add Symptoms**: Click on search suggestions to add them
- **Remove Symptoms**: Click the "×" on any symptom tag to remove it

#### Step 2: Run Diagnosis
- Click **"🧠 Diagnose Disease"** button
- Wait for Bayesian analysis (typically 50-200ms)
- View results with visual charts and probability rankings

#### Step 3: Interpret Results
- **Probability Bar**: Visual representation of disease likelihood
- **Confidence Score**: Based on symptom coverage
- **Matching Symptoms**: Shows which symptoms match
- **Orpha Code**: Official Orphanet disease identifier
- **Chart**: Top 5 diseases with probability visualization

## Example Usage Scenarios

### Scenario 1: Neurological Symptoms
**Present Symptoms:**
- Seizure
- Intellectual disability
- Macrocephaly

**Expected Results:**
- Alexander disease (high probability)
- Various epilepsy syndromes
- Metabolic disorders

### Scenario 2: Muscle Weakness
**Present Symptoms:**
- Muscle weakness
- Fatigue
- Difficulty walking

**Absent Symptoms:**
- Fever
- Rash

### Scenario 3: Growth Disorders
**Present Symptoms:**
- Short stature
- Delayed puberty
- Intellectual disability

## API Endpoints for Developers

### GET `/symptoms`
Search available symptoms:
```bash
curl "http://localhost:8000/symptoms?search=seizure&limit=10"
```

### GET `/diseases`
Browse diseases:
```bash
curl "http://localhost:8000/diseases?search=alexander&limit=5"
```

### POST `/diagnose`
Perform diagnosis:
```bash
curl -X POST "http://localhost:8000/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "present_symptoms": ["Seizure", "Intellectual disability"],
    "absent_symptoms": ["Fever"],
    "top_n": 10
  }'
```

### GET `/health`
Check API status:
```bash
curl "http://localhost:8000/health"
```

### GET `/info`
Get system statistics:
```bash
curl "http://localhost:8000/info"
```

## Understanding the Bayesian Algorithm

### How It Works
1. **Prior Probability**: Each disease starts with equal likelihood
2. **Present Symptoms**: Multiply by symptom frequency in disease
3. **Absent Symptoms**: Multiply by (1 - symptom frequency)
4. **Posterior**: Final probability after Bayesian inference

### Frequency Mapping
- **Very frequent (99-80%)**: 0.9 probability
- **Frequent (79-30%)**: 0.55 probability  
- **Occasional (29-5%)**: 0.17 probability
- **Very rare (<5%)**: 0.025 probability
- **Unknown frequency**: 0.5 probability

### Confidence Score
- Based on symptom coverage: `matching_symptoms / total_present_symptoms`
- Higher confidence = more symptoms matched
- Range: 0.0 to 1.0

## Data Sources

### Orphanet Database
- **4,281 rare diseases** from Orphanet
- **8,595 unique symptoms** (HPO terms)
- **114,961 disease-symptom associations**
- Frequency data for each association

### File Structure
```
clinical_signs_and_symptoms_in_rare_diseases.csv
├── disorder_id: Unique identifier
├── orpha_code: Orphanet code
├── disorder_name: Disease name
├── hpo_id: HPO term ID
├── hpo_term: Symptom name
├── hpo_frequency: Frequency category
└── diagnostic_criteria: Additional info
```

## Troubleshooting

### Common Issues

**1. API Connection Error**
```
Error: Failed to load symptoms. Please ensure the API is running on localhost:8000
```
**Solution**: Run `python3 start_interface.py`

**2. CSV File Not Found**
```
Error: CSV data file not found
```
**Solution**: Ensure `file/clinical_signs_and_symptoms_in_rare_diseases.csv` exists

**3. No Results Found**
```
No matching diseases found for the selected symptoms
```
**Solution**: 
- Try more common symptoms
- Check symptom spelling
- Reduce number of absent symptoms

**4. Slow Performance**
```
Processing time > 1000ms
```
**Solution**:
- Reduce `top_n` parameter
- Use fewer symptoms
- Check system resources

### Browser Compatibility
- **Chrome**: ✅ Fully supported
- **Firefox**: ✅ Fully supported  
- **Safari**: ✅ Fully supported
- **Edge**: ✅ Fully supported
- **Mobile**: ✅ Responsive design

## Advanced Usage

### Custom Deployment
```bash
# Production deployment
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker deployment
docker-compose up -d

# Cloud deployment
./deploy.sh
```

### API Integration
```python
import requests

# Initialize API client
api = requests.Session()
api.headers.update({'Content-Type': 'application/json'})

# Perform diagnosis
response = api.post('http://localhost:8000/diagnose', json={
    'present_symptoms': ['Seizure', 'Intellectual disability'],
    'top_n': 5
})

results = response.json()
```

### Batch Processing
```python
# Process multiple patients
patients = [
    {'present_symptoms': ['Seizure', 'Intellectual disability']},
    {'present_symptoms': ['Muscle weakness', 'Fatigue']},
    # ... more patients
]

for i, patient in enumerate(patients):
    response = api.post('http://localhost:8000/diagnose', json=patient)
    print(f"Patient {i+1}: {response.json()['results'][0]['disorder_name']}")
```

## Performance Metrics

### Typical Performance
- **Startup Time**: 2-3 seconds (data loading)
- **Diagnosis Time**: 50-200ms per request
- **Memory Usage**: ~500MB with full dataset
- **Concurrent Users**: 100+ (with proper deployment)

### Optimization Tips
1. Use `top_n` parameter to limit results
2. Cache frequent symptom searches
3. Deploy with multiple workers for production
4. Use CDN for static assets

## Support & Documentation

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Demo Script**: `python3 demo_api.py`

## Next Steps

1. **Customize Symptoms**: Add your own symptom database
2. **Enhance Algorithm**: Implement more sophisticated Bayesian models
3. **Add Features**: Patient history, multiple diseases, severity scores
4. **Scale Deployment**: Use Kubernetes, load balancers, databases
5. **Integrate Systems**: Connect to EHR, clinical decision support tools