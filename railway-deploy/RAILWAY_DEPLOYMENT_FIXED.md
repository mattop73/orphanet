# Railway Deployment - Fixed Version

## Issues Fixed

1. **❌ Fixed:** Hardcoded `localhost:8000` API URLs in HTML files
   - Now uses `window.location.origin` to dynamically determine the API base URL
   
2. **❌ Fixed:** Unnecessary `start.py` wrapper
   - Now uses `main.py` directly via Procfile
   
3. **❌ Fixed:** Incorrect PORT environment variable handling
   - Now properly uses Railway's `PORT` environment variable
   
4. **❌ Fixed:** CORS configuration issues
   - Updated CORS middleware for better production compatibility

## Key Changes Made

### 1. HTML Files Updated
```javascript
// OLD (causing localhost errors):
const API_BASE = 'http://localhost:8000';

// NEW (works in production):
const API_BASE = window.location.origin;
```

### 2. Procfile Simplified
```
# OLD:
web: python start.py

# NEW:
web: python main.py
```

### 3. Main.py Enhanced
- Added proper PORT environment variable handling
- Improved logging for debugging
- Better error handling for CSV file loading
- Enhanced CORS configuration

## Deployment Steps

1. **Deploy to Railway:**
   ```bash
   # From the railway-deploy directory
   railway up
   ```

2. **Verify Deployment:**
   ```bash
   # Test locally first:
   python main.py
   
   # Test with the test script:
   python test_deployment.py
   
   # Test production URL:
   python test_deployment.py https://your-app.railway.app
   ```

3. **Check Logs:**
   ```bash
   railway logs
   ```

## Expected Behavior

- ✅ Server starts on Railway's assigned PORT
- ✅ Frontend loads without localhost errors
- ✅ API endpoints respond correctly
- ✅ Symptom loading works from production URL
- ✅ Diagnosis functionality works

## Testing Endpoints

Once deployed, these endpoints should work:

- `https://your-app.railway.app/` - Main interface
- `https://your-app.railway.app/health` - Health check
- `https://your-app.railway.app/symptoms?limit=10` - Symptoms API
- `https://your-app.railway.app/diagnose` - Diagnosis API

## Troubleshooting

If you still get errors:

1. **Check Railway logs:**
   ```bash
   railway logs --tail
   ```

2. **Verify CSV file is deployed:**
   - Make sure `file/clinical_signs_and_symptoms_in_rare_diseases.csv` exists in the deployment

3. **Test individual endpoints:**
   ```bash
   curl https://your-app.railway.app/health
   curl https://your-app.railway.app/symptoms?limit=5
   ```

4. **Check browser console:**
   - Open browser dev tools
   - Look for any remaining localhost references
   - Check network tab for failed requests

## Files Modified

- ✅ `index.html` - Fixed API_BASE URL
- ✅ `symptom_selector.html` - Fixed API_BASE URL  
- ✅ `Procfile` - Simplified to use main.py directly
- ✅ `main.py` - Enhanced for Railway deployment
- ❌ `start.py` - Removed (no longer needed)

The deployment should now work correctly without the localhost and 502 errors!