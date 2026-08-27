@echo off
setlocal enabledelayedexpansion
title AetherClean (Windows 11 Edition)

echo =======================================================
echo          AetherClean - System Storage Analyzer
echo =======================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in your PATH!
    echo.
    echo Please install Python 3.10 or newer:
    echo 1. Download from https://www.python.org/downloads/
    echo 2. IMPORTANT: Check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check if required libraries are installed
python -c "import PySide6, psutil, yaml, send2trash" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Required libraries (PySide6, psutil, pyyaml, send2trash) are missing.
    echo [SETUP] Installing dependencies automatically... Please wait.
    echo.
    python -m pip install -r "%~dp0requirements.txt"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies. Please check your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [SETUP] Dependencies successfully installed!
    echo.
)

:: 3. Launch Application
echo Starting AetherClean...
python "%~dp0main.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] An unexpected error occurred while running AetherClean.
    pause
)
