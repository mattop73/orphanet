# 🌐 Orphanet API Frontend Guide

## 🎉 **Frontend is Now Working!**

The Content Security Policy (CSP) issue has been resolved. Your interactive web interface is fully functional!

## 🚀 **How to Access the Frontend**

### Option 1: Direct URL
Open your browser and go to:
```
http://localhost:3000/index.html
```

### Option 2: Use the Launcher Script
```bash
./start-frontend.sh
```
This script will:
- Check server status
- Open the frontend in your default browser
- Show you useful URLs and test commands

### Option 3: Test Script
```bash
node test-frontend.js
```
This runs comprehensive tests and confirms everything is working.

## 🎯 **Frontend Features**

### 📊 **Interactive API Testing**
- **Health Check**: Test server status
- **Database Statistics**: View data counts for all tables
- **Disorder Browsing**: List and paginate through 11,238+ disorders
- **Search Functionality**: Search disorders by name (e.g., "alexander", "syndrome")
- **Gene Data**: Browse 2,208+ genes with chromosomal locations
- **HPO Terms**: Clinical signs and symptoms data

### 🔍 **Real-Time Testing**
Each API endpoint has a "Test" button that:
- Makes live API calls
- Shows response data in formatted JSON
- Displays success/error status with color coding
- Shows pagination information

### 📱 **Responsive Design**
- Works on desktop, tablet, and mobile
- Clean, modern interface
- Easy-to-read results
- Color-coded status indicators

## 🧪 **What You Can Test**

### 1. **System Information**
- `/health` - Server health check
- `/api/stats` - Database statistics

### 2. **Disorder Data**
- `/api/disorders?limit=5` - List disorders
- `/api/disorders/58` - Get Alexander disease details
- `/api/disorders/search/alexander` - Search for Alexander diseases

### 3. **Gene Information**
- `/api/genes?limit=5` - List genes
- `/api/genes/GFAP` - Get specific gene (if exists)

### 4. **HPO Terms**
- `/api/hpo-terms?limit=5` - Clinical signs and symptoms

## 📊 **Current Database Content**

Your API currently serves:
- **11,238 Disorders** with full metadata
- **2,208 Genes** with chromosomal locations
- **1,021 Disorder Synonyms**
- **11,401 Age of Onset** records
- **6,679 Inheritance Types**
- **40,375 External References**
- **34,899 Disability Associations**
- **19,535 Classifications**

## 🎨 **Interface Features**

### Visual Indicators
- ✅ **Green**: Successful API calls
- ❌ **Red**: Error responses
- ⏳ **Yellow**: Loading state

### Interactive Elements
- **Test Buttons**: Click to make API calls
- **Expandable Results**: JSON responses in formatted view
- **Real-time Status**: Live server connectivity

### Sample Data Display
- Shows first result from API calls
- Pagination information
- Item counts and totals

## 🔧 **Troubleshooting**

### If Frontend Doesn't Load
1. Ensure server is running: `curl http://localhost:3000/health`
2. Check port 3000 isn't blocked
3. Try restarting: `pkill -f "node server.js" && node server.js`

### If API Calls Fail
1. Check server logs in terminal
2. Verify Supabase credentials in `.env`
3. Test individual endpoints with curl

### If CSP Errors Return
The server is now configured to allow inline scripts. If you see CSP errors:
1. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)
2. Clear browser cache
3. Check browser console for specific errors

## 🎯 **Next Steps**

### For Development
- Modify `public/index.html` to customize the interface
- Add new endpoints in `server.js`
- Update styling in the `<style>` section

### For Production
- Consider separating CSS/JS into external files
- Add authentication if needed
- Implement rate limiting
- Add more sophisticated error handling

## 🌟 **Success!**

Your Orphanet API frontend is now fully operational! You can:
- Browse rare disease data interactively
- Test all API endpoints in real-time
- Search and filter through comprehensive medical data
- Access detailed disorder information with prevalence data

**Enjoy exploring your rare disease database! 🧬**