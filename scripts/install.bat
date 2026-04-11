@echo off
REM Windows batch script to install Markdown Viewer

echo ============================================================
echo   MARKDOWN VIEWER - Windows Installation Script
echo ============================================================
echo.

REM Check if Poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Poetry is not installed. Installing Poetry...
    pip install poetry
    if %errorlevel% neq 0 (
        echo Error: Failed to install Poetry
        pause
        exit /b 1
    )
)

echo Installing Python dependencies with Poetry...
poetry install
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Installing Playwright browsers...
poetry run playwright install
if %errorlevel% neq 0 (
    echo Warning: Playwright browser installation failed
    echo PDF export may not work
)

echo.
echo Checking for Node.js and npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: npm not found!
    echo Please install Node.js from https://nodejs.org/
    echo Electron GUI will not be available without Node.js
    pause
) else (
    echo Installing Electron dependencies...
    cd ..\markdown_viewer\electron
    call npm install
    if %errorlevel% neq 0 (
        echo Warning: Failed to install Electron dependencies
        echo GUI may not work properly
    )
    cd ..\..\..
)

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo To start Markdown Viewer:
echo   poetry run markdown-viewer
echo.
echo Or activate the virtual environment:
echo   poetry shell
echo   markdown-viewer
echo.
pause
