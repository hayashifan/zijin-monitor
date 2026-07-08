@echo off
REM 紫金监控器开机自启开关
REM 删除 auto_start 文件即可禁用: del auto_start
REM 创建 auto_start 文件即可启用: type nul > auto_start

cd /d "%~dp0"
if not exist auto_start (
    echo [紫金监控器] auto_start 不存在，跳过自启
    exit /b 0
)
echo [紫金监控器] 检测到 auto_start，正在启动...
pm2 resurrect
echo [紫金监控器] 启动完成
