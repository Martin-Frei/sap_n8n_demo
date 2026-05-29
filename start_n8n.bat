
@echo off

REM   .\start_n8n.bat
REM   Startet n8n + Flask Prediction Server



echo ============================================================
echo    SAP Fraud Detection Pipeline
echo    n8n + Flask Prediction Server
echo ============================================================

echo.
echo Starte n8n Server (neues Fenster)...
start "n8n Server" "C:\Users\tsinn\AppData\Roaming\fnm\node-versions\v22.22.3\installation\node.exe" "C:\Users\tsinn\AppData\Local\npm-cache\_npx\a8a7eec953f1f314\node_modules\n8n\bin\n8n"

echo Starte Flask Prediction Server...
timeout /t 3 >nul
cd /d C:\Users\tsinn\VSCode\Repos\sap_n8n_demo
call venv_sap\Scripts\activate
python python\predict\predict_server.py