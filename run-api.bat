@echo off
REM Tiny launcher for the FinOps API + dashboard. Double-click to run.
setlocal
cd /d "%~dp0services\api-service"

echo ---------------------------------------------------------------
echo  FinOps API + dashboard
echo  Dashboard : http://127.0.0.1:8000
echo  API docs  : http://127.0.0.1:8000/docs
echo  (Close this window or press Ctrl+C to stop the server.)
echo ---------------------------------------------------------------

REM Open the dashboard in the default browser, then start the server.
start "" http://127.0.0.1:8000
api-service --db-path ../ingestion-service/data/finops.db

echo.
echo Server stopped.
pause
