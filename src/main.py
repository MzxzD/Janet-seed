#!/usr/bin/env python3
"""
J.A.N.E.T. Seed — Constitutional AI Companion
Entry point for bootstrap and initialization
"""

import sys
import json
import argparse
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Import our modules
from hardware_detector import HardwareDetector, generate_capability_report
from constitution_loader import Constitution, ConstitutionalGuard
from installer import Installer

# Import core module (Janet's sacred cognitive core)
from core import JanetCore, run_presence_loop, run_conversation_loop

# Voice I/O (Day 2) - Optional imports (for voice mode detection)
try:
    from voice import SpeechToText, TextToSpeech, WakeWordDetector, ToneAwareness
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️  Voice I/O not available (optional Day 2 feature)")


class VerificationLogger:
    """Encrypted log for constitutional verification."""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # For Day 1, use simple encryption (in production would use proper key management)
        self.key = self._derive_key()
    
    def _derive_key(self) -> bytes:
        """Derive encryption key (simplified for Day 1)."""
        # In production, use proper key derivation
        return hashlib.sha256(b"janet_verification_log_key").digest()
    
    def log_verification(self, verified: bool, constitution_hash: str):
        """Log verification result (simplified - full encryption in production)."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "verified": verified,
            "hash": constitution_hash
        }
        
        try:
            # Append to log file (in production would encrypt)
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except (OSError, IOError) as e:
            print(f"⚠️  Failed to log verification: {e}")
            # Non-critical, continue without logging


def present_constitutional_briefing(axioms: list, hardware_fingerprint: str) -> bool:
    """Display axioms and request consent with hardware fingerprint."""
    print("\n" + "="*60)
    print("J.A.N.E.T. SEED CONSTITUTIONAL BRIEFING")
    print("="*60)
    
    print("\nJ.A.N.E.T. Seed operates under foundational axioms, including:")
    for i, axiom in enumerate(axioms[:5], 1):  # Show first 5
        print(f"{i}. {axiom}")
    
    if len(axioms) > 5:
        print(f"... and {len(axioms) - 5} more")
    
    print("\n" + "-"*60)
    print("KEY PRINCIPLES:")
    print("- Red Thread: 'red thread' stops everything immediately")
    print("- Soul Check: verification before significant changes")
    print("- Secrets Sacred: private conversations stay private")
    print("- Consent Required: J.A.N.E.T. Seed grows only with your permission")
    
    print("\n" + "="*60)
    print("J.A.N.E.T. Seed will install with minimal capabilities:")
    print("- Text conversation only")
    print("- Red Thread emergency stop")
    print("- Ephemeral memory (forgets when closed)")
    print("- No voice, no delegation, no network access")
    print("\nNothing will be installed without your explicit consent.")
    print("="*60)
    
    while True:
        choice = input("\nOptions:\n  [s]how all axioms\n  [y]es - I consent\n  [n]o - I do not consent\n\nYour choice: ").strip().lower()
        
        if choice in ["s", "show"]:
            print("\n" + "="*60)
            print("ALL CONSTITUTIONAL AXIOMS")
            print("="*60)
            for i, axiom in enumerate(axioms, 1):
                print(f"{i}. {axiom}")
            print("="*60)
            continue
        elif choice in ["yes", "y"]:
            return True
        elif choice in ["no", "n", ""]:
            return False
        else:
            print("Please choose 's' to show axioms, 'y' for yes, or 'n' for no.")


def save_consent(hardware_profile: Dict, hardware_fingerprint: str, config_path: Path):
    """Save consent record with timestamp and hardware fingerprint."""
    consent_data = {
        "consented_at": datetime.utcnow().isoformat() + "Z",
        "hardware_fingerprint": hardware_fingerprint,
        "hardware_summary": {
            "platform": hardware_profile.get("platform", "unknown"),
            "capability_level": hardware_profile.get("capability_level", "unknown")
        }
    }
    
    try:
        config_path.mkdir(parents=True, exist_ok=True)
        consent_file = config_path / "consent.json"
        with open(consent_file, 'w') as f:
            json.dump(consent_data, f, indent=2)
    except (OSError, IOError) as e:
        print(f"⚠️  Failed to save consent: {e}")
        print("   Continuing without saving consent record")
        raise  # Re-raise since consent saving is critical


def generate_hardware_fingerprint(hardware_dict: Dict) -> str:
    """Generate SHA-256 fingerprint of hardware profile."""
    fingerprint_data = json.dumps(hardware_dict, sort_keys=True)
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def save_hardware_report(report: Dict, config_path: Path):
    """Save hardware capability report."""
    try:
        config_path.mkdir(parents=True, exist_ok=True)
        report_file = config_path / "hardware_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
    except (OSError, IOError) as e:
        print(f"⚠️  Failed to save hardware report: {e}")
        # Non-critical, continue without saving report


def get_janet_home() -> Path:
    """Get Janet home directory."""
    if "JANET_HOME" in os.environ:
        return Path(os.environ["JANET_HOME"]).expanduser().resolve()
    
    # Try to get home directory
    try:
        home_dir = Path.home()
    except (RuntimeError, KeyError) as e:
        # Fallback if home directory cannot be determined
        raise RuntimeError(f"Cannot determine home directory: {e}. Please set JANET_HOME environment variable.")
    
    return (home_dir / ".janet").resolve()


def get_constitution_path(janet_home: Optional[Path] = None) -> Path:
    """Get constitution file path - works both for installation and runtime."""
    if janet_home and (janet_home / "constitution" / "personality.json").exists():
        return janet_home / "constitution" / "personality.json"
    
    # Fall back to source directory
    source_dir = Path(__file__).parent.parent
    return source_dir / "constitution" / "personality.json"


def main():
    """Bootstrap entry point for J.A.N.E.T. Seed."""
    parser = argparse.ArgumentParser(description="J.A.N.E.T. Seed - Constitutional AI Companion")
    parser.add_argument("--detect-only", action="store_true", help="Only detect hardware and exit")
    parser.add_argument("--verify", action="store_true", help="Verify constitution and exit")
    parser.add_argument("--voice", action="store_true", help="Enable voice I/O mode (Day 2)")
    args = parser.parse_args()
    
    # Get paths
    source_dir = Path(__file__).parent.parent
    janet_home = get_janet_home()
    constitution_path = get_constitution_path(janet_home)
    
    # 1. Hardware detection
    print("🌱 J.A.N.E.T. Seed Bootstrap")
    print("="*40)
    print("\nDetecting hardware...")
    
    hardware_profile_obj = HardwareDetector.detect()
    hardware_dict = hardware_profile_obj.to_dict()
    hardware_report = generate_capability_report()
    
    # Save hardware report
    save_hardware_report(hardware_report, janet_home / "config")
    
    print(f"\nHardware detected:")
    print(f"  Platform: {hardware_profile_obj.platform} {hardware_profile_obj.platform_version}")
    print(f"  Architecture: {hardware_profile_obj.architecture}")
    print(f"  Memory: {hardware_profile_obj.memory_gb:.1f} GB")
    print(f"  Disk free: {hardware_profile_obj.disk_free_gb:.1f} GB")
    print(f"  CPU cores: {hardware_profile_obj.cpu_cores_physical} physical, {hardware_profile_obj.cpu_cores_logical} logical")
    print(f"  GPU: {'Yes' if hardware_profile_obj.gpu_available else 'No'} ({hardware_profile_obj.gpu_vendor or 'None'})")
    print(f"  Network: {hardware_report.get('network_access', 'offline only')}")
    print(f"  Janet capability: {hardware_profile_obj.capability_level()}")
    
    # Handle --detect-only
    if args.detect_only:
        print("\n" + json.dumps(hardware_report, indent=2))
        sys.exit(0)
    
    # 2. Load and verify constitution
    print("\nLoading constitution...")
    try:
        constitution = Constitution.load(str(constitution_path))
        print(f"✅ Constitution loaded ({len(constitution.axioms)} axioms)")
        
        # Verify constitution integrity (fail fast if compromised)
        if not constitution.verify():
            print("\n❌ Constitutional integrity compromised! Aborting.")
            sys.exit(1)
        
        print("✅ Constitutional integrity verified")
        
    except FileNotFoundError:
        print(f"\n❌ Constitution not found at: {constitution_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error loading constitution: {e}")
        sys.exit(1)
    
    # Handle --verify
    if args.verify:
        print("\n✅ Constitution verification passed")
        sys.exit(0)
    
    # Set up verification logging
    verifier_logger = VerificationLogger(janet_home / "logs" / "verification.log.enc")
    verifier_logger.log_verification(True, constitution.original_hash)
    
    # Set up Constitutional Guard (handles daily checks)
    guard = ConstitutionalGuard(str(constitution_path))
    
    # 3. Check for existing installation
    installer = Installer(str(janet_home), str(source_dir))
    is_installed = installer.is_installed()
    
    # 4. Consent dialog (if not already consented)
    consent_file = janet_home / "config" / "consent.json"
    has_consent = consent_file.exists()
    
    if not has_consent:
        hardware_fingerprint = generate_hardware_fingerprint(hardware_dict)
        if not present_constitutional_briefing(constitution.axioms, hardware_fingerprint):
            print("\nConsent not given. Exiting cleanly.")
            sys.exit(0)
        
        # Save consent
        save_consent(hardware_report, hardware_fingerprint, janet_home / "config")
        print("\n✅ Consent recorded")
    else:
        print("\n✅ Previous consent found")
    
    # 5. Installation (if not already installed)
    if not is_installed:
        if not installer.install(hardware_dict, constitution.original_hash):
            print("\n❌ Installation failed. Exiting.")
            sys.exit(1)
    else:
        print("\n✅ J.A.N.E.T. Seed already installed")
    
    # 6. Launch J.A.N.E.T. Seed Core
    # Determine voice mode: default to True (voice mode) if voice is available
    # --voice flag explicitly enables, but defaults to True if available
    voice_mode = VOICE_AVAILABLE  # Default to voice mode if available
    # If --voice flag is explicitly provided, use it (but still respect VOICE_AVAILABLE)
    if args.voice:
        voice_mode = VOICE_AVAILABLE  # --voice means "use voice if available"
    
    print("\n🌱 J.A.N.E.T. Seed Active")
    if voice_mode:
        print("🎤 Voice mode enabled")
        print("Say 'Hey Janet' to wake me up, or speak directly.")
    else:
        print("Type 'red thread' to invoke emergency stop.")
        print("Type 'quit' to exit.")
        if args.voice and not VOICE_AVAILABLE:
            print("⚠️  Voice mode requested but not available (install voice dependencies)")
    print("-"*40)
    
    # Initialize memory directory
    memory_dir = janet_home / "memory"
    
        # Load expansion state (Day 5)
        from expansion import ExpansionStateManager
        expansion_state_manager = ExpansionStateManager(janet_home / "config")
        expansion_state = expansion_state_manager.load_expansion_state()
        
        # Initialize Janet Core with expansion support
        janet = JanetCore(
            str(constitution_path),
            guard,
            voice_mode=voice_mode,
            memory_dir=memory_dir,
            config_path=janet_home / "config",
            hardware_profile=hardware_profile_obj
        )
    
    # Start wake word detection if in voice mode (for Presence Loop)
    if voice_mode and janet.wake_detector and janet.wake_detector.is_available():
        janet.wake_detector.start_listening()
        print("👂 Listening for wake word 'Hey Janet'...")
    
        # Main loop: Presence Loop -> Conversation Loop
        last_daily_check = datetime.utcnow()
        
        while True:
            try:
                # Daily constitutional verification (Axiom 7: Constitutional Integrity)
                now = datetime.utcnow()
                if (now - last_daily_check).total_seconds() >= 86400:  # 24 hours
                    try:
                        guard.daily_check()
                        last_daily_check = now
                        print("✅ Daily constitutional verification completed")
                    except RuntimeError as e:
                        print(f"\n⚠️  Constitutional verification failed: {e}")
                        print("Janet will continue operating, but please investigate this issue.")
                        # Don't crash - allow user to continue but warn them
                    except Exception as e:
                        print(f"\n⚠️  Error during daily verification: {e}")
                        # Continue operation
                
                # Run Presence Loop (wake word, greeting, device selection)
                input_device = run_presence_loop(janet, voice_mode)
                
                # Run Conversation Loop (structured conversation flow)
                result = run_conversation_loop(janet, input_device, voice_mode)
            
            # Handle conversation loop return value
            if result == "quit":
                # User wants to exit entirely
                break
            elif result:
                # Conversation complete, return to Presence Loop
                continue
            else:
                # Continue conversation loop (shouldn't normally happen)
                continue
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            if not janet.red_thread_active:
                print("Type 'red thread' if you need to stop everything.")
            
            # Cleanup wake detector on error (attempt, but continue loop)
            try:
                if voice_mode and janet.wake_detector:
                    janet.wake_detector.stop_listening()
            except Exception as cleanup_error:
                print(f"⚠️  Cleanup error: {cleanup_error}")
    
    # Cleanup
    if voice_mode and janet.wake_detector:
        janet.wake_detector.stop_listening()


if __name__ == "__main__":
    main()
