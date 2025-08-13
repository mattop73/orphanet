# ✅ Railway Deployment Checklist

## Pre-Deployment Verification

- [x] **Core Files Present**
  - [x] `start.py` - Railway entry point
  - [x] `main.py` - FastAPI application
  - [x] `local_fast_diagnosis.py` - Diagnosis logic
  - [x] `index.html` - Enhanced web interface with clickable links
  - [x] `symptom_selector.html` - Simple interface
  - [x] `file/clinical_signs_and_symptoms_in_rare_diseases.csv` - Disease data

- [x] **Configuration Files**
  - [x] `requirements.txt` - Python dependencies
  - [x] `railway.toml` - Railway configuration
  - [x] `Procfile` - Process definition
  - [x] `runtime.txt` - Python version
  - [x] `.gitignore` - Git ignore rules

- [x] **Documentation**
  - [x] `README.md` - Deployment guide
  - [x] `DEPLOYMENT_CHECKLIST.md` - This checklist

## Railway Deployment Steps

### 1. Upload to Railway
- [ ] Go to [Railway.app](https://railway.app)
- [ ] Create new project
- [ ] Upload `railway-deploy` folder or connect GitHub repo
- [ ] Select this folder as root directory

### 2. Verify Automatic Detection
Railway should automatically:
- [ ] Detect Python application
- [ ] Find `requirements.txt`
- [ ] Use `start.py` as entry point (via Procfile)
- [ ] Set Python version from `runtime.txt`

### 3. Monitor Deployment
- [ ] Check build logs for errors
- [ ] Verify all dependencies install successfully
- [ ] Confirm app starts without errors
- [ ] Wait for health check to pass

### 4. Test Deployed Application
- [ ] Visit Railway-provided URL
- [ ] Verify main interface loads (`/`)
- [ ] Test symptom selector interface (`/selector`)
- [ ] Check API documentation (`/docs`)
- [ ] Verify health endpoint (`/health`)

### 5. Test Enhanced Features
- [ ] Select symptoms and run diagnosis
- [ ] Verify disease predictions appear
- [ ] **Test clickable links** - click on disease cards
- [ ] Confirm Orphanet pages open in new tabs
- [ ] Verify links use correct format: `https://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert={orpha_code}`

### 6. Performance Verification
- [ ] Diagnosis completes in reasonable time (1-5 seconds)
- [ ] Interface is responsive
- [ ] No console errors in browser
- [ ] All features work as expected

## Troubleshooting

### Common Issues and Solutions

**Build Fails:**
- Check `requirements.txt` for correct package versions
- Verify Python version in `runtime.txt` is supported
- Review Railway build logs for specific errors

**App Won't Start:**
- Ensure `start.py` imports work correctly
- Check that CSV file is in correct location
- Verify PORT environment variable usage

**Features Not Working:**
- Test locally first: `python start.py`
- Check browser console for JavaScript errors
- Verify API endpoints respond correctly

**Links Not Working:**
- Confirm `orpha_code` values in CSV are correct
- Test Orphanet URL format manually
- Check browser network tab for failed requests

## Success Criteria

✅ **Deployment Successful When:**
- Railway build completes without errors
- Application starts and health check passes
- Web interface loads and displays correctly
- Disease diagnosis functionality works
- **Clickable disease links redirect to Orphanet**
- All interfaces (main and selector) function properly
- API documentation is accessible
- Performance is acceptable for production use

## Post-Deployment

- [ ] Share Railway URL with stakeholders
- [ ] Monitor application performance
- [ ] Set up custom domain (optional)
- [ ] Configure auto-scaling if needed
- [ ] Document any environment-specific configurations

---

**🚀 Ready for Railway deployment!**

**Key Features:**
- ✨ Enhanced disease diagnosis with clickable Orphanet links
- 🌐 Two web interfaces (full and simple)
- 📊 Real-time disease probability calculations
- 🔗 Direct integration with official Orphanet database
- 📱 Responsive design for all devices