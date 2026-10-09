@echo off
echo ========================================================
echo   Starting VIT MAPATHON Agricultural GIS Platform
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "FastAPI Backend" cmd /k "python -m uvicorn main:app --app-dir member1-ml/backend --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting React + Leaflet Frontend on http://localhost:5174 ...
start "React Frontend" cmd /k "cd member2-gis\frontend && npm run dev"

echo.
echo ========================================================
echo   Both services launched in separate windows!
echo   - Web GIS Dashboard: http://localhost:5174
echo   - Backend Swagger:   http://127.0.0.1:8000/docs
echo ========================================================
