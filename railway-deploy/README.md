# 🚀 Bayesian Disease Diagnosis API - Railway Deployment

This folder contains all the necessary files to deploy the Bayesian Disease Diagnosis API with clickable Orphanet links to Railway.

## 📁 **Files Included**

```
railway-deploy/
├── start.py                    # Railway entry point
├── main.py                     # FastAPI application
├── local_fast_diagnosis.py     # Local diagnosis logic
├── index.html                  # Enhanced web interface with clickable links
├── symptom_selector.html       # Simple symptom selector interface
├── requirements.txt            # Python dependencies
├── railway.toml               # Railway configuration
├── Procfile                   # Process file for Railway
├── runtime.txt                # Python version specification
├── file/
│   └── clinical_signs_and_symptoms_in_rare_diseases.csv  # Disease data
└── README.md                  # This file
```

## 🚀 **Deploy to Railway**

### **Step 1: Upload to Railway**
1. Go to [Railway.app](https://railway.app)
2. Create a new project
3. Upload this entire `railway-deploy` folder
4. Or connect your GitHub repository and point to this folder

### **Step 2: Railway will automatically:**
- ✅ Detect Python application
- ✅ Install dependencies from `requirements.txt`
- ✅ Start the app using `start.py`
- ✅ Provide a public URL

### **Step 3: Environment Variables (Optional)**
No environment variables are required for basic deployment. The app uses local CSV data.

## 🌐 **API Endpoints**

Once deployed, your API will have:

- `GET /` - Enhanced web interface with clickable disease links
- `GET /selector` - Simple symptom selector interface  
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /diagnose` - Disease diagnosis endpoint
- `GET /symptoms` - Get symptoms with search
- `GET /diseases` - Get diseases with search

## ✨ **New Features**

### **Clickable Disease Links**
- Each disease prediction is now clickable
- Links directly to official Orphanet disease pages
- Format: `https://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert={orpha_code}`
- Opens in new tab to preserve diagnosis results

### **Enhanced User Experience**
- Visual indicators (🔗) show clickable diseases
- Hover effects for better interaction
- Helpful tips guide users to click for more info
- Maintains beautiful existing design

## 🔧 **Local Testing**

To test locally before deployment:

```bash
cd railway-deploy
pip install -r requirements.txt
python start.py
```

Visit `http://localhost:8000` to see the interface.

## 📊 **Performance**

- **Diagnosis Time**: ~1-5 seconds (local CSV processing)
- **Symptoms Endpoint**: ~100ms
- **Health Check**: ~10ms
- **Memory Usage**: ~200MB

## 🛠️ **Troubleshooting**

**Common Issues:**

1. **"CSV file not found"**
   - Ensure `file/clinical_signs_and_symptoms_in_rare_diseases.csv` exists
   - Check file path in deployment

2. **"Import error"**
   - Verify all Python files are included
   - Check `requirements.txt` has all dependencies

3. **"Port binding error"**
   - Railway automatically sets PORT environment variable
   - App uses PORT from environment or defaults to 8000

## 🎯 **Success Indicators**

After deployment:
- ✅ `/health` endpoint returns 200 OK
- ✅ Web interface loads at your Railway URL
- ✅ Disease predictions are clickable
- ✅ Orphanet links open correctly
- ✅ Diagnosis works with selected symptoms

## 🆘 **Support**

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **API Documentation**: Visit `/docs` on your deployed URL
- **Health Check**: Visit `/health` to verify deployment

---

**🚀 Ready to deploy your enhanced disease diagnosis API with clickable Orphanet links!**