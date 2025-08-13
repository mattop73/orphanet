# Supabase Setup for Railway Deployment

## Overview

The application now uses Supabase instead of CSV files for both fast and true Bayesian diagnosis modes. This provides better performance, scalability, and eliminates the need for large CSV files in the deployment.

## Required Environment Variables

Set these in your Railway project environment:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### Getting Your Supabase Credentials

1. **Go to your Supabase project dashboard**
2. **Settings → API**
3. **Copy the values:**
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_KEY`

## Required Database Tables

The application expects these Supabase tables to exist:

### Core Tables (Required)
- `disorders` - Disease information
- `hpo_terms` - HPO symptom terms  
- `hpo_associations` - Disease-symptom associations

### Optimized Tables (Optional but Recommended)
- `fast_symptoms` - Pre-computed symptom data
- `fast_diseases` - Pre-computed disease data
- `fast_probabilities` - Pre-computed probability matrices
- `disorder_symptoms_view` - Optimized view for queries

## Database Schema

### Core Tables
```sql
-- Disorders table
CREATE TABLE disorders (
    id SERIAL PRIMARY KEY,
    disorder_name TEXT NOT NULL,
    orpha_code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HPO Terms table  
CREATE TABLE hpo_terms (
    id SERIAL PRIMARY KEY,
    hpo_term TEXT UNIQUE NOT NULL,
    hpo_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HPO Associations table
CREATE TABLE hpo_associations (
    id SERIAL PRIMARY KEY,
    disorder_id INTEGER REFERENCES disorders(id),
    hpo_term_id INTEGER REFERENCES hpo_terms(id),
    hpo_frequency TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Optimized view for fast queries
CREATE VIEW disorder_symptoms_view AS
SELECT 
    d.disorder_name,
    d.orpha_code,
    h.hpo_term,
    a.hpo_frequency
FROM disorders d
JOIN hpo_associations a ON d.id = a.disorder_id
JOIN hpo_terms h ON h.id = a.hpo_term_id;
```

## How It Works

### Fast Mode (`computation_mode: "fast"`)
1. Uses `fast_probabilities` table if available
2. Falls back to `disorder_symptoms_view` for basic queries
3. Pre-computed probabilities for instant results (~100ms)

### True Mode (`computation_mode: "true"`)
1. Fetches ALL disease-symptom associations from Supabase
2. Performs full Bayesian computation with proper normalization
3. Evaluates every disease in the database (~5-30s)
4. Most mathematically accurate results

## Performance Optimization

### Indexes (Recommended)
```sql
-- Core indexes
CREATE INDEX idx_disorders_name ON disorders(disorder_name);
CREATE INDEX idx_disorders_orpha ON disorders(orpha_code);
CREATE INDEX idx_hpo_terms_term ON hpo_terms(hpo_term);
CREATE INDEX idx_hpo_associations_disorder ON hpo_associations(disorder_id);
CREATE INDEX idx_hpo_associations_hpo ON hpo_associations(hpo_term_id);

-- Fast table indexes (if using optimized tables)
CREATE INDEX idx_fast_probabilities_symptom ON fast_probabilities(symptom_name);
CREATE INDEX idx_fast_probabilities_disease ON fast_probabilities(disease_name);
CREATE INDEX idx_fast_probabilities_probability ON fast_probabilities(probability DESC);
```

### Row Level Security (RLS)

Make sure your tables have appropriate RLS policies:

```sql
-- Enable RLS
ALTER TABLE disorders ENABLE ROW LEVEL SECURITY;
ALTER TABLE hpo_terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE hpo_associations ENABLE ROW LEVEL SECURITY;

-- Allow read access for anon users
CREATE POLICY "Allow read access" ON disorders FOR SELECT USING (true);
CREATE POLICY "Allow read access" ON hpo_terms FOR SELECT USING (true);  
CREATE POLICY "Allow read access" ON hpo_associations FOR SELECT USING (true);
```

## Testing

Use the provided test script:

```bash
# Test locally
python test_supabase_integration.py

# Test production
python test_supabase_integration.py https://your-app.railway.app
```

## Troubleshooting

### Client Library Issues

If you get errors like `TypeError: Client.__init__() got an unexpected keyword argument 'proxy'`:

1. **The application automatically falls back** to a simple HTTP-based client
2. **This is normal** and doesn't affect functionality
3. **Both clients provide the same features** - the simple one just uses direct HTTP requests

### Common Issues

1. **Connection Failed**
   - Check SUPABASE_URL and SUPABASE_KEY
   - Verify your Supabase project is active
   - Check network connectivity
   - Try the test script: `python test_both_supabase_versions.py`

2. **Permission Denied**
   - Review RLS policies
   - Make sure anon key has read permissions
   - Check table permissions

3. **Table Not Found**
   - Verify required tables exist
   - Check table names match exactly
   - Ensure view `disorder_symptoms_view` exists

4. **Slow Performance**
   - Add recommended indexes
   - Consider using fast_* tables for pre-computed data
   - Check query execution plans

5. **Library Version Conflicts**
   - The app includes two Supabase clients (full and simple)
   - Simple client uses direct HTTP requests (more reliable)
   - Both provide identical functionality

### Error Messages

- `"Supabase diagnosis system not ready"` → Check connection and environment variables
- `"None of the provided symptoms are found"` → Verify symptom data exists in database
- `"No disease-symptom data found"` → Check that tables have data

## Migration from CSV

If migrating from CSV-based deployment:

1. **Load your CSV data into Supabase** using provided loader scripts
2. **Set environment variables** in Railway
3. **Deploy updated code** with Supabase integration
4. **Remove CSV files** from deployment (no longer needed)

## Benefits of Supabase Integration

✅ **No large CSV files in deployment**
✅ **Better performance with proper indexing**
✅ **Real-time data updates possible**
✅ **Scalable database backend**
✅ **True Bayesian computation on full dataset**
✅ **Optimized fast mode with pre-computed probabilities**