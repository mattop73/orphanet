# Computation Modes Feature

## Overview

The Bayesian Disease Diagnosis API now supports two computation modes for calculating disease probabilities:

- **🚀 Fast Mode**: Uses pre-computed probabilities for quick results (~100ms)
- **🧮 True Mode**: Full Bayesian computation with proper normalization (~5-30s)

## Frontend Interface

### Main Interface (`/`)

The main interface includes a computation mode switch located between the symptom type toggles and the symptom search:

```
⚡ Computation Mode    [FAST ←→ TRUE]
```

- **Green (left)**: Fast mode - Pre-computed probabilities
- **Red (right)**: True Bayesian mode - Full normalization computation

The interface automatically updates to show:
- Expected processing time
- Description of the selected mode
- Results include the computation mode used

### Simple Selector (`/selector`)

The simple selector always uses Fast mode by default for quick results.

## API Changes

### Request Format

The `/diagnose` endpoint now accepts an additional parameter:

```json
{
    "present_symptoms": ["Seizure", "Intellectual disability"],
    "absent_symptoms": ["Fever"],
    "top_n": 10,
    "computation_mode": "fast"  // "fast" or "true"
}
```

### Response Format

The response now includes the computation mode used:

```json
{
    "success": true,
    "results": [...],
    "total_diseases_evaluated": 4000,
    "input_symptoms": ["Seizure", "Intellectual disability"],
    "processing_time_ms": 125.5,
    "computation_mode": "fast"  // Shows which mode was actually used
}
```

## Computation Modes Explained

### Fast Mode (`"fast"`)

- **Method**: Uses pre-computed probability tables
- **Speed**: ~100-500ms
- **Accuracy**: Good for most use cases
- **Coverage**: Limited to diseases with pre-computed data
- **Use Case**: Quick diagnoses, real-time applications

**Algorithm**:
1. Looks up pre-computed probabilities
2. Simple scoring based on symptom matches
3. Fast sorting and ranking

### True Bayesian Mode (`"true"`)

- **Method**: Full Bayesian inference with proper normalization
- **Speed**: ~5-30 seconds (depending on dataset size)
- **Accuracy**: Most mathematically accurate
- **Coverage**: All diseases in the database
- **Use Case**: Research, detailed analysis, maximum accuracy

**Algorithm**:
1. Calculates P(disease|symptoms) using Bayes' theorem
2. Computes evidence P(symptoms) by summing over ALL diseases
3. Proper normalization ensures probabilities sum to 1
4. Evaluates every disease in the database

**Mathematical Details**:
```
P(disease|symptoms) = P(symptoms|disease) × P(disease) / P(symptoms)

Where:
- P(symptoms|disease): Likelihood based on symptom frequencies
- P(disease): Prior probability based on disease prevalence in dataset
- P(symptoms): Evidence calculated by summing over all diseases
```

## Performance Comparison

| Mode | Processing Time | Diseases Evaluated | Normalization | Accuracy |
|------|----------------|-------------------|---------------|----------|
| Fast | 100-500ms | ~100-500 | Approximate | Good |
| True | 5-30 seconds | ALL (~4000+) | Exact | Best |

## Usage Guidelines

### When to Use Fast Mode
- ✅ Real-time applications
- ✅ Quick screenings
- ✅ Interactive demos
- ✅ Mobile applications
- ✅ High-traffic scenarios

### When to Use True Mode
- ✅ Research applications
- ✅ Detailed clinical analysis
- ✅ Maximum accuracy needed
- ✅ Comprehensive evaluations
- ✅ Academic studies

## Testing

Use the provided test script to verify both modes:

```bash
# Test locally
python test_computation_modes.py

# Test production
python test_computation_modes.py https://your-app.railway.app
```

Expected results:
- Fast mode: < 1 second response time
- True mode: 5-30 seconds response time
- Both modes return valid results with correct computation_mode field

## Frontend Implementation

### JavaScript Functions

```javascript
// Get current computation mode
function getComputationMode() {
    const switchElement = document.getElementById('computation-mode-switch');
    return switchElement.checked ? 'true' : 'fast';
}

// Update mode information
function updateComputationModeInfo(isTrueMode) {
    // Updates the description text based on selected mode
}
```

### CSS Classes

```css
.computation-mode-section { /* Main container */ }
.computation-mode-switch { /* Toggle switch */ }
.computation-slider { /* Switch slider */ }
.mode-fast { color: #28a745; } /* Fast mode styling */
.mode-true { color: #dc3545; } /* True mode styling */
```

## Error Handling

- Invalid computation_mode values default to "fast"
- Timeout handling: 30s for fast mode, 60s for true mode
- Graceful fallback if true mode fails

## Future Enhancements

Potential improvements:
- Caching for true mode results
- Partial computation for faster true mode
- Hybrid mode combining both approaches
- Progress indicators for true mode
- Batch processing for multiple symptom sets