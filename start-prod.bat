@echo off
chcp 65001 >nul 2>&1
title Zijin Monitor - Production

echo ========================================
echo   Zijin Monitor - Production Start
echo ========================================

REM Set environment
set NODE_ENV=production

REM Start PM2 with ecosystem config
echo Starting services via PM2...
cd /d "%~dp0"
pm2 start ecosystem.config.cjs

REM Show status
echo.
echo ========================================
pm2 status
echo ========================================

echo.
echo   Backend:  http://localhost:3001
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Useful commands:
echo   pm2 logs zijin-server   - View backend logs
echo   pm2 logs zijin-web      - View frontend logs
echo   pm2 restart all         - Restart all services
echo   pm2 stop all            - Stop all services
echo   pm2 delete all          - Remove all services
echo.
pause
