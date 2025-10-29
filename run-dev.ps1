Start-Process powershell -ArgumentList "cd apps/api; .\.venv\Scripts\Activate.ps1; python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Minimized
Start-Process powershell -ArgumentList "cd apps/web; npm run dev" -WindowStyle Minimized

