# Windows Installation Guide

J.A.N.E.T. Seed runs on Windows 10/11 with some platform-specific considerations.

## Prerequisites

### Minimum Requirements
- **Windows 10** (Version 1909+) or **Windows 11**
- **8 GB RAM** (16 GB recommended)
- **10 GB free disk space**
- **Python 3.11+**
- **PowerShell 5.1+**

### Recommended Setup
For best experience, we recommend:
1. **WSL2** (Windows Subsystem for Linux 2)
2. **Windows Terminal** (from Microsoft Store)
3. **Administrator access** (for full feature set)

## Installation Methods

### Method 1: Full Installer (Recommended)
1. Download the J.A.N.E.T. Seed package
2. Right-click `install.bat` → **"Run as Administrator"**
3. Follow the prompts

### Method 2: Manual Installation
If the installer fails:
1. Install Python from [python.org](https://python.org)
2. Install Ollama from [ollama.com/download/windows](https://ollama.com/download/windows)
3. Clone the repository:
   ```powershell
   git clone https://github.com/your-org/janet-seed.git
   cd janet-seed
   ```
4. Run the bootstrap manually:
   ```powershell
   .\install.ps1
   ```

## WSL2 vs Native Windows

### WSL2 Mode (Recommended)
- **Better performance** for AI models
- **Full Linux compatibility**
- **GPU acceleration** (with NVIDIA CUDA in WSL2)
- **Simpler dependency management**

To enable:
```powershell
# Install WSL2
winget install --id Microsoft.WSL --source winget

# Restart and run Janet in WSL2 mode
janet --wsl
```

### Native Windows Mode
- **No WSL2 required**
- **Limited model performance**
- **Some features may be unavailable**
- **Manual dependency installation**

## Known Windows-Specific Issues

### 1. Microphone Access
Windows requires explicit app permissions:
1. Settings → Privacy & Security → Microphone
2. Enable "Allow apps to access your microphone"
3. For Janet specifically, may need to:
   ```powershell
   # Grant microphone access
   Get-AppxPackage -AllUsers | Where-Object {$_.Name -like "*WindowsStore*"} | Foreach-Object {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\AppXManifest.xml"}
   ```

### 2. GPU Acceleration
For NVIDIA GPUs in WSL2:
```powershell
# Install NVIDIA CUDA drivers for WSL2
# From: https://developer.nvidia.com/cuda-downloads
# Select "WSL-Ubuntu" as target
```

### 3. Firewall Rules
Janet may need firewall exceptions:
```powershell
# Allow local Janet communication
New-NetFirewallRule -DisplayName "Janet Local" -Direction Inbound -Protocol TCP -LocalPort 8000-8010 -Action Allow
```

## Running Janet

### Start Methods:
```powershell
# Method 1: PowerShell (recommended)
.\start-janet.ps1

# Method 2: Command Prompt
start-janet.bat

# Method 3: Desktop shortcut
# Double-click "Janet Seed" on desktop

# Method 4: From anywhere (if added to PATH)
janet
```

### Common Commands:
```bash
# Check installation
janet --verify

# Hardware detection
janet --detect

# Constitutional verification
janet --check-constitution

# Red Thread test
# Type "red thread" during conversation
```

## Troubleshooting

### "Python not found"
```powershell
# Reinstall Python
winget install Python.Python.3.11

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

### "Ollama service not running"
```powershell
# Start Ollama service
Start-Service -Name Ollama

# Or restart if needed
Restart-Service -Name Ollama
```

### "Permission denied"
- Run PowerShell as **Administrator**
- Check User Account Control (UAC) settings
- Verify file permissions in `%USERPROFILE%\.janet\`

### "Model download failed"
```powershell
# Manual model download
ollama pull tinyllama:1.1b --insecure

# Or use a different model
ollama pull gemma:2b
```

## Uninstallation

Complete removal:
```powershell
# From Janet directory
.\uninstall.ps1

# Or manually
Remove-Item -Path "$env:USERPROFILE\.janet" -Recurse -Force
Remove-Item -Path "$env:USERPROFILE\Desktop\Janet Seed.lnk" -Force
```

## Support

For Windows-specific issues:
1. Check Windows Event Viewer for errors
2. Enable debug logging: `janet --debug`
3. Review logs in `%USERPROFILE%\.janet\logs\`

Remember: Janet is offline-first. No data leaves your machine.

