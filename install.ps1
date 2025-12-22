# J.A.N.E.T. Seed Bootstrap Installer for Windows
# Run in PowerShell as Administrator: .\install.ps1

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

# Configuration
$JanetHome = "$env:USERPROFILE\.janet"
$InstallDir = $PSScriptRoot
$PythonVersion = "3.11"  # Minimum required

# Colors for better UX
$Host.UI.RawUI.ForegroundColor = "Cyan"
Write-Host "🚀 J.A.N.E.T. Seed Bootstrap for Windows" -ForegroundColor Green
Write-Host "========================================"
$Host.UI.RawUI.ForegroundColor = "Gray"

# Check for existing installation
if (Test-Path $JanetHome) {
    if (Test-Path "$JanetHome\config\installation.json") {
        Write-Host "⚠️  Existing Janet installation found at $JanetHome" -ForegroundColor Yellow
        $response = Read-Host "Do you want to remove it and reinstall? (yes/NO)"
        if ($response -eq "yes") {
            Write-Host "Removing existing installation..."
            Remove-Item -Path $JanetHome -Recurse -Force
        } else {
            Write-Host "Installation cancelled." -ForegroundColor Red
            exit 1
        }
    }
}

# Check WSL2 (recommended for best experience)
function Test-WSL2 {
    try {
        $wsl = wsl --list --quiet 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

if (-not (Test-WSL2)) {
    Write-Host "⚠️  WSL2 not detected." -ForegroundColor Yellow
    Write-Host "For best experience, we recommend installing WSL2:"
    Write-Host "  winget install --id Microsoft.WSL --source winget"
    Write-Host "Janet will run in Windows-native mode (limited features)."
    
    $response = Read-Host "Continue with Windows-native installation? (yes/NO)"
    if ($response -ne "yes") {
        exit 1
    }
}

# Check Python (required before running main.py)
function Test-Python {
    try {
        $python = python --version 2>&1
        return $python -match "Python 3\.[0-9]+\.[0-9]+"
    } catch {
        return $false
    }
}

if (-not (Test-Python)) {
    Write-Host "Python not found or outdated." -ForegroundColor Yellow
    Write-Host "Installing Python $PythonVersion via winget..."
    
    try {
        winget install --id Python.Python.$PythonVersion --source winget
        Write-Host "✅ Python installed successfully." -ForegroundColor Green
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } catch {
        Write-Host "Failed to install Python automatically." -ForegroundColor Red
        Write-Host "Please install Python manually from: https://www.python.org/downloads/"
        Write-Host "Then run this installer again."
        exit 1
    }
}

# Check for psutil (basic dependency for hardware detection)
try {
    python -c "import psutil" 2>$null
} catch {
    Write-Host "Installing basic dependencies..." -ForegroundColor Yellow
    python -m pip install --user psutil 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Could not install psutil. Installation may fail." -ForegroundColor Yellow
    }
}

# Create desktop shortcut (optional)
if (Test-Path "$env:USERPROFILE\Desktop") {
    $shortcutPath = "$env:USERPROFILE\Desktop\Janet Seed.lnk"
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-NoExit -File `"$JanetHome\start-janet.ps1`""
    $Shortcut.WorkingDirectory = $JanetHome
    $Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,24"  # Chat icon
    $Shortcut.Description = "Janet Seed - Constitutional AI Companion"
    $Shortcut.Save()
    
    Write-Host "✅ Desktop shortcut created." -ForegroundColor Green
}

# Add to PATH (user only)
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$JanetHome*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$JanetHome", "User")
    Write-Host "✅ Added Janet to PATH (user)." -ForegroundColor Green
}

# Run main.py which handles the full installation flow
Write-Host ""
Write-Host "Starting Janet installation process..."
Write-Host ""
python "$InstallDir\src\main.py"

# Installation complete message is handled by main.py

# Pause so user can read (if running in console)
if ($Host.Name -eq "ConsoleHost") {
    Write-Host ""
    Write-Host "Press any key to continue..."
    $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
}