@echo off
cd /d "E:\GROUPS\THE LEGACY CIRCLE GROUP\TLC_PORTAL"

if not exist "data\cloudflare" mkdir "data\cloudflare"

echo Waiting for TLC Flask server...

:WAIT_FOR_TLC
powershell.exe -NoProfile -Command "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/status' -UseBasicParsing -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"

if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto WAIT_FOR_TLC
)

echo TLC Flask server is online.
echo Starting Cloudflare Quick Tunnel...

cloudflared tunnel --url http://127.0.0.1:5000 > "data\cloudflare\tunnel.log" 2>&1
