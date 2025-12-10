@echo off
title Trading Service
setlocal
echo ============================================================
echo   Start Trading Service
echo ============================================================
echo.

set "logFolder=logs"

if exist "%logFolder%" (
    echo Clearing all .log files in %logFolder%...
    del /q "%logFolder%\*.log" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Operation completed successfully.
    ) else (
        echo No .log files found or error occurred.
    )
) else (
    echo Folder "%logFolder%" does not exist.
)
endlocal

echo Start trading service...
call .venv\Scripts\activate && python main.py --config=./config/config_td.yaml --app_type=td"

echo.
echo ============================================================
echo   Trading service launched successfully£¡
echo ============================================================
echo.
pause > nul

