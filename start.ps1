# CollegeMarketingAI — One-click startup script
# Starts both backend (FastAPI :8000) and frontend (Vite :5173)

Write-Host "=== CollegeMarketingAI Startup ===" -ForegroundColor Cyan

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Install Python 3.11+ from python.org" -ForegroundColor Red
    exit 1
}

# Check Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js not found. Install from nodejs.org" -ForegroundColor Red
    exit 1
}

# Create .env if missing
if (-not (Test-Path "backend\.env")) {
    Copy-Item ".env.example" "backend\.env"
    Write-Host "Created backend\.env from template. Fill in GMAIL_APP_PASSWORD before sending campaigns." -ForegroundColor Yellow
}

# Install backend dependencies
Write-Host "`n[1/3] Installing backend dependencies..." -ForegroundColor Green
Push-Location backend
pip install -r requirements.txt -q
Pop-Location

# Install frontend dependencies
Write-Host "[2/3] Installing frontend dependencies..." -ForegroundColor Green
Push-Location frontend
npm install --silent
Pop-Location

Write-Host "[3/3] Starting servers..." -ForegroundColor Green

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$PWD\backend'; Write-Host 'Backend starting on http://127.0.0.1:8000' -ForegroundColor Cyan; python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$PWD\frontend'; Write-Host 'Frontend starting on http://localhost:5173' -ForegroundColor Cyan; npm run dev"

Write-Host "`nBoth servers launched in separate windows." -ForegroundColor Green
Write-Host "Open http://localhost:5173 in your browser." -ForegroundColor Cyan
Write-Host "`nBackend API docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
