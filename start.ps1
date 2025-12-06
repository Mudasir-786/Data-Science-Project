# Start script for AQI Monitoring System
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AQI Monitoring & Prediction System" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install/Update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r backend\requirements.txt

# Start the Flask application
Write-Host ""
Write-Host "Starting Flask server..." -ForegroundColor Green
Write-Host "Access the dashboard at: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
cd backend
python app.py
