# start_demo.ps1
# Helper script to install dependencies and start the iTantra M3 Web Demo

Write-Host "=================================================="
Write-Host "   iTantra M3 Protocol Demo - Startup Script"
Write-Host "=================================================="

# 1. Start Backend
Write-Host "Starting FastAPI Backend..."
cd "C:\Users\parth\Downloads\itantra-m3\web-demo\backend"
python -m pip install -r requirements.txt
Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Normal

# 2. Start Frontend
Write-Host "Starting React Frontend..."
cd "C:\Users\parth\Downloads\itantra-m3\web-demo\frontend"
npm install
Start-Process -FilePath "npm" -ArgumentList "run dev" -WindowStyle Normal

Write-Host "=================================================="
Write-Host "   Demo starting in background windows."
Write-Host "   Backend API: http://localhost:8000"
Write-Host "   Frontend UI: http://localhost:5173"
Write-Host "=================================================="
