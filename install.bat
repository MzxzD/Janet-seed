@echo off
REM J.A.N.E.T. Seed Bootstrap Installer Wrapper
REM Run this as Administrator

echo.
echo ⚠️  J.A.N.E.T. Seed Bootstrap for Windows
echo ========================================
echo.

REM Check for PowerShell
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PowerShell is required but not found.
    echo Please install PowerShell and try again.
    pause
    exit /b 1
)

REM Check if running as Administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ This installer requires Administrator privileges.
    echo Please right-click and "Run as Administrator".
    pause
    exit /b 1
)

REM Run PowerShell installer
echo 🚀 Starting Janet installation...
echo This may take a few minutes...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Installation failed with error code: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ✅ Installation complete!
echo.
pause