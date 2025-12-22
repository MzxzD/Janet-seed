"""
Hardware detection for capability-aware installation.
"""
import platform
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import psutil

@dataclass
class HardwareProfile:
    """System capabilities profile."""
    platform: str
    platform_version: str
    architecture: str
    memory_gb: float
    disk_free_gb: float
    cpu_cores_physical: int
    cpu_cores_logical: int
    gpu_available: bool
    gpu_vendor: Optional[str]
    gpu_memory_gb: Optional[float]
    
    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            "platform": self.platform,
            "platform_version": self.platform_version,
            "architecture": self.architecture,
            "memory_gb": round(self.memory_gb, 1),
            "disk_free_gb": round(self.disk_free_gb, 1),
            "cpu_cores_physical": self.cpu_cores_physical,
            "cpu_cores_logical": self.cpu_cores_logical,
            "gpu_available": self.gpu_available,
            "gpu_vendor": self.gpu_vendor,
            "gpu_memory_gb": self.gpu_memory_gb
        }
    
    def capability_level(self) -> str:
        """
        Determine what Janet can run on this hardware.
        Returns: "minimal", "basic", "standard", or "advanced"
        """
        if self.memory_gb < 4:
            return "minimal"    # Text only, 3B model
        elif self.memory_gb < 8:
            return "basic"      # + voice, 7B model
        elif self.memory_gb < 16:
            return "standard"   # + memory, delegation
        else:
            return "advanced"   # + expansion, multiple models
    
    def can_run_feature(self, feature: str) -> bool:
        """Check if hardware supports a specific feature."""
        feature_requirements = {
            "text": {"memory": 2, "disk": 1},
            "voice_stt": {"memory": 4, "disk": 2},
            "voice_tts": {"memory": 4, "disk": 1},
            "memory_persistence": {"memory": 6, "disk": 5},
            "delegation": {"memory": 8, "disk": 3},
            "vision": {"memory": 8, "gpu": True, "disk": 2},
            "multiple_models": {"memory": 16, "disk": 10},
        }
        
        if feature not in feature_requirements:
            return False
        
        req = feature_requirements[feature]
        
        if self.memory_gb < req.get("memory", 0):
            return False
        
        if self.disk_free_gb < req.get("disk", 0):
            return False
        
        if req.get("gpu", False) and not self.gpu_available:
            return False
        
        return True

class HardwareDetector:
    """Cross-platform hardware detection."""
    
    @staticmethod
    def detect() -> HardwareProfile:
        """Main detection method."""
        system = platform.system()
        
        if system == "Darwin":
            return HardwareDetector._detect_macos()
        elif system == "Linux":
            return HardwareDetector._detect_linux()
        elif system == "Windows":
            return HardwareDetector._detect_windows()
        else:
            return HardwareDetector._detect_generic()
    
    @staticmethod
    def _detect_generic() -> HardwareProfile:
        """Fallback detection for unknown platforms."""
        return HardwareProfile(
            platform=platform.system(),
            platform_version=platform.version(),
            architecture=platform.machine(),
            memory_gb=psutil.virtual_memory().total / 1e9,
            disk_free_gb=psutil.disk_usage("/").free / 1e9,
            cpu_cores_physical=psutil.cpu_count(logical=False) or 1,
            cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
            gpu_available=False,
            gpu_vendor=None,
            gpu_memory_gb=None
        )
    
    @staticmethod
    def _detect_macos() -> HardwareProfile:
        """macOS-specific hardware detection."""
        import platform as pl
        
        # Try to get GPU info
        gpu_available = False
        gpu_vendor = None
        gpu_memory = None
        
        try:
            # Try system_profiler for Apple Silicon
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Chipset Model" in result.stdout:
                gpu_available = True
                gpu_vendor = "Apple"
                # Parse memory if available
                for line in result.stdout.split('\n'):
                    if "VRAM" in line:
                        try:
                            gpu_memory = float(line.split()[-2])
                        except:
                            pass
        except:
            pass
        
        return HardwareProfile(
            platform="macOS",
            platform_version=pl.mac_ver()[0],
            architecture=platform.machine(),
            memory_gb=psutil.virtual_memory().total / 1e9,
            disk_free_gb=psutil.disk_usage("/").free / 1e9,
            cpu_cores_physical=psutil.cpu_count(logical=False) or 1,
            cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
            gpu_available=gpu_available,
            gpu_vendor=gpu_vendor,
            gpu_memory_gb=gpu_memory
        )
    
    @staticmethod
    def _detect_linux() -> HardwareProfile:
        """Linux-specific hardware detection."""
        gpu_available = False
        gpu_vendor = None
        gpu_memory = None
        
        try:
            # Check for NVIDIA
            nvidia_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if nvidia_result.returncode == 0:
                gpu_available = True
                gpu_vendor = "NVIDIA"
                # Parse first line
                lines = nvidia_result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(',')
                    if len(parts) > 1:
                        try:
                            gpu_memory = float(parts[1].strip().split()[0])
                        except:
                            pass
        except:
            pass
        
        return HardwareProfile(
            platform="Linux",
            platform_version=platform.version(),
            architecture=platform.machine(),
            memory_gb=psutil.virtual_memory().total / 1e9,
            disk_free_gb=psutil.disk_usage("/").free / 1e9,
            cpu_cores_physical=psutil.cpu_count(logical=False) or 1,
            cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
            gpu_available=gpu_available,
            gpu_vendor=gpu_vendor,
            gpu_memory_gb=gpu_memory
        )
    
    @staticmethod
    def _detect_windows() -> HardwareProfile:
        """Windows-specific hardware detection."""
        # For WSL2, treat as Linux
        if "microsoft" in platform.version().lower():
            return HardwareDetector._detect_linux()
        
        # Native Windows
        import ctypes
        
        gpu_available = False
        gpu_vendor = None
        
        try:
            # Simple check for display adapter
            result = subprocess.run(
                ["wmic", "path", "win32_videocontroller", "get", "name"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            if result.returncode == 0 and "NVIDIA" in result.stdout:
                gpu_available = True
                gpu_vendor = "NVIDIA"
        except:
            pass
        
        return HardwareProfile(
            platform="Windows",
            platform_version=platform.version(),
            architecture=platform.machine(),
            memory_gb=psutil.virtual_memory().total / 1e9,
            disk_free_gb=psutil.disk_usage("/").free / 1e9,
            cpu_cores_physical=psutil.cpu_count(logical=False) or 1,
            cpu_cores_logical=psutil.cpu_count(logical=True) or 1,
            gpu_available=gpu_available,
            gpu_vendor=gpu_vendor,
            gpu_memory_gb=None
        )
    
    @staticmethod
    def _recommend_model_size(hardware: HardwareProfile) -> str:
        """Recommend appropriate model size based on hardware."""
        if hardware.memory_gb < 4:
            return "3B"
        elif hardware.memory_gb < 8:
            return "7B"
        elif hardware.memory_gb < 16:
            return "13B"
        else:
            return "70B"
    
    @staticmethod
    def _estimate_max_tasks(hardware: HardwareProfile) -> int:
        """Estimate maximum concurrent tasks based on hardware."""
        # Simple heuristic: more memory/cores = more tasks
        base_tasks = 1
        memory_multiplier = hardware.memory_gb / 4  # 1 task per 4GB
        core_multiplier = hardware.cpu_cores_logical / 2  # 1 task per 2 cores
        return max(1, int(base_tasks + memory_multiplier + core_multiplier))

def generate_capability_report() -> Dict:
    """Generate a comprehensive capability report."""
    hardware = HardwareDetector.detect()
    
    capabilities = {
        "text_conversation": hardware.can_run_feature("text"),
        "voice_stt": hardware.can_run_feature("voice_stt"),
        "voice_tts": hardware.can_run_feature("voice_tts"),
        "memory_persistence": hardware.can_run_feature("memory_persistence"),
        "delegation": hardware.can_run_feature("delegation"),
        "vision": hardware.can_run_feature("vision"),
        "multiple_models": hardware.can_run_feature("multiple_models"),
    }
    
    return {
        "hardware": hardware.to_dict(),
        "capability_level": hardware.capability_level(),
        "capabilities": capabilities,
        "network_access": "offline only",  # Janet operates offline-first
        "recommended_model_size": HardwareDetector._recommend_model_size(hardware),
        "estimated_max_concurrent_tasks": HardwareDetector._estimate_max_tasks(hardware)
    }

if __name__ == "__main__":
    # Command-line interface
    import json
    
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        report = generate_capability_report()
        print(json.dumps(report, indent=2))
    else:
        hardware = HardwareDetector.detect()
        print("Hardware Detection Report")
        print("=" * 40)
        print(f"Platform: {hardware.platform} {hardware.platform_version}")
        print(f"Architecture: {hardware.architecture}")
        print(f"Memory: {hardware.memory_gb:.1f} GB")
        print(f"Disk free: {hardware.disk_free_gb:.1f} GB")
        print(f"CPU cores: {hardware.cpu_cores_physical} physical, {hardware.cpu_cores_logical} logical")
        print(f"GPU: {'Yes' if hardware.gpu_available else 'No'} ({hardware.gpu_vendor or 'None'})")
        if hardware.gpu_memory_gb:
            print(f"GPU memory: {hardware.gpu_memory_gb} GB")
        print(f"\nJanet capability level: {hardware.capability_level()}")
