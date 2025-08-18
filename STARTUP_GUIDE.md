# PDF Analysis Workbench - Startup Guide

## 🚀 Running Backend and Frontend in Separate Terminals

### Method 1: Using Batch Files (Windows)

**Terminal 1 - Backend:**

```cmd
start_backend.bat
```

**Terminal 2 - Frontend:**

```cmd
start_frontend.bat
```

### Method 2: Using PowerShell Scripts

**Terminal 1 - Backend:**

```powershell
.\start_backend.ps1
```

**Terminal 2 - Frontend:**

```powershell
.\start_frontend.ps1
```

### Method 3: Manual Commands

**Terminal 1 - Backend:**

```cmd
conda activate .\.conda
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**

```cmd
conda activate .\.conda
streamlit run frontend/main.py --server.port 8080 --server.address 0.0.0.0
```

## 📋 Step-by-Step Instructions

### 1. Start Backend First

1. Open **Terminal 1** (Command Prompt or PowerShell)
2. Navigate to the project directory
3. Run one of the backend startup commands above
4. Wait for the message: "Uvicorn running on http://0.0.0.0:8000"
5. Backend will be available at: http://localhost:8000

### 2. Start Frontend Second

1. Open **Terminal 2** (Command Prompt or PowerShell)
2. Navigate to the project directory
3. Run one of the frontend startup commands above
4. Wait for the message: "You can now view your Streamlit app in your browser"
5. Frontend will be available at: http://localhost:8080

## 🔍 Health Checks

### Backend Health Check

Visit: http://localhost:8000/health
Expected response: `{"status": "healthy"}`

### Frontend Health Check

Visit: http://localhost:8080
Expected: PDF Analysis Workbench interface loads

## 🛠️ Troubleshooting

### Backend Issues

**Port 8000 already in use:**

```cmd
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**Conda environment not found:**

```cmd
# Recreate environment
conda env create -f environment.yml
# or
conda create -p .\.conda python=3.11
conda activate .\.conda
pip install -r requirements.txt
```

### Frontend Issues

**Port 8080 already in use:**

```cmd
# Use different port
streamlit run frontend/main.py --server.port 8081
```

**Backend connection failed:**

- Ensure backend is running on port 8000
- Check firewall settings
- Verify backend health endpoint

## 🎯 Testing Text Selection

Once both services are running:

1. **Open browser**: http://localhost:8080
2. **Upload PDF**: Use the upload interface
3. **Test selection**:
   - Click and drag to select text
   - Verify selection starts exactly at click point
   - Verify only text between anchor and pointer is selected
   - Check for clean selection without artifacts

## 📊 Service URLs

| Service        | URL                          | Purpose             |
| -------------- | ---------------------------- | ------------------- |
| Backend API    | http://localhost:8000        | FastAPI backend     |
| Backend Health | http://localhost:8000/health | Health check        |
| Backend Docs   | http://localhost:8000/docs   | API documentation   |
| Frontend App   | http://localhost:8080        | Streamlit interface |

## 🔧 Development Mode

Both services run in development mode with auto-reload:

- **Backend**: Changes to Python files trigger automatic restart
- **Frontend**: Streamlit auto-reloads on file changes

## 🛑 Stopping Services

**To stop either service:**

- Press `Ctrl+C` in the respective terminal
- Or close the terminal window

**To stop all services:**

```cmd
# Kill all Python processes (use with caution)
taskkill /F /IM python.exe
```

## 🔍 Testing Search Engine Console Output

The backend now prints detailed search results to the console! You can test this in several ways:

### Method 1: Direct Test Scripts

```cmd
# Test with sample data and see console output
python test_console_search_demo.py
```

### Method 2: API Testing

When the backend is running, search API calls will print detailed results:

```cmd
# Start backend and watch console for search output
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Then make API calls to see console output:

- `POST /search/enhanced` - Enhanced multi-tier search
- `POST /search/related-content` - Related content search
- `POST /search/semantic` - Basic semantic search

### Console Output Features

The console will show:

- 🔍 **Search Query**: What was searched for
- ⏱️ **Search Time**: How long the search took
- 📄 **Results**: Document, section, confidence scores
- 📝 **Snippets**: Relevant text excerpts
- 📊 **Statistics**: Cache hits, search performance
- 🎯 **Search Tier**: Fast vs precision search used

### Example Console Output

```
================================================================================
🔍 SEMANTIC SEARCH RESULTS
================================================================================
Query: 'machine learning patterns'
Search Time: 37.9ms
Results Found: 1
Confidence Threshold: 0.5

📄 Result #1
   Document: demo_doc
   Section: ml_intro
   Page: 1
   Type: paragraph
   Similarity: 0.689
   Confidence: 0.758
   Search Tier: precision
   📝 Snippet: Machine learning algorithms analyze large datasets...

📊 Search Statistics:
   Cache Hit Rate: 0.0%
   Precision Search Rate: 100.0%
   Average Search Time: 37.9ms
   Total Searches: 1
================================================================================
```

## 📝 Logs

**Backend logs**: Displayed in Terminal 1 (includes search results!)
**Frontend logs**: Displayed in Terminal 2

Both services provide detailed logging for debugging.
