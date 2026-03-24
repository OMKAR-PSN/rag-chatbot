# start.ps1
Write-Host "Starting India Innovates RAG System..." -ForegroundColor Green

# Start Backend API
Start-Process powershell -ArgumentList "-NoExit -Command `"cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload`"" -WindowStyle Normal

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit -Command `"cd frontend; npm run dev`"" -WindowStyle Normal

Write-Host "Servers are starting in separate windows." -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor Cyan
