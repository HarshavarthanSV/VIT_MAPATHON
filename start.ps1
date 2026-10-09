Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting VIT MAPATHON Agricultural GIS Platform" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn main:app --app-dir member1-ml/backend --host 127.0.0.1 --port 8000 --reload"

Write-Host "[2/2] Starting React + Leaflet Frontend on http://localhost:5174..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd member2-gis\frontend; npm run dev"

Write-Host "`nServices started!" -ForegroundColor Green
Write-Host "  Dashboard: http://localhost:5174" -ForegroundColor Yellow
Write-Host "  API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor Yellow
