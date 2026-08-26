@echo off
title AetherClean
echo Starting AetherClean...
python "%~dp0main.py"
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while launching AetherClean.
    pause
)
