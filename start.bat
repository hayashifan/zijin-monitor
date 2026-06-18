@echo off
chcp 65001 >nul 2>&1
title Zijin Monitor

echo ========================================
echo   Zijin Stock Monitor - Starting...
echo ========================================

REM Start backend
echo [1/2] Starting backend on port 3001...
cd /d "%~dp0backend"
start "Backend" ./venv/Scripts/python.exe main.py
timeout /t 2 /nobreak >nul

REM Start frontend
echo [2/2] Starting frontend...
cd /d "%~dp0frontend"
start "Frontend" cmd /k "npm run dev"

echo ========================================
echo   Services started!
echo   Backend:  http://localhost:3001
echo   Frontend: http://localhost:5173
echo ========================================
timeout /t 5 /nobreak >nul
start http://localhost:5173
echo Press any key to close...
pause >nul
