"""
Unit tests for Expansion State Manager
"""
import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expansion.expansion_state import ExpansionState, ExpansionStateManager
from expansion.expansion_types import ExpansionType


class TestExpansionState(unittest.TestCase):
    """Test expansion state data class."""
    
    def test_initialization(self):
        """Test state initialization."""
        state = ExpansionState()
        
        self.assertEqual(len(state.enabled_expansions), 0)
        self.assertEqual(len(state.consent_records), 0)
    
    def test_is_enabled(self):
        """Test checking if expansion is enabled."""
        state = ExpansionState()
        
        self.assertFalse(state.is_enabled(ExpansionType.VOICE_IO))
        
        state.enabled_expansions[ExpansionType.VOICE_IO] = {"config": "test"}
        self.assertTrue(state.is_enabled(ExpansionType.VOICE_IO))
    
    def test_get_config(self):
        """Test getting expansion configuration."""
        state = ExpansionState()
        
        self.assertIsNone(state.get_config(ExpansionType.VOICE_IO))
        
        config = {"voice_model": "whisper"}
        state.enabled_expansions[ExpansionType.VOICE_IO] = config
        self.assertEqual(state.get_config(ExpansionType.VOICE_IO), config)
    
    def test_enable(self):
        """Test enabling an expansion."""
        state = ExpansionState()
        
        config = {"voice_model": "whisper"}
        consent_data = {
            "hardware_fingerprint": "test_fingerprint",
            "user_consent": True
        }
        
        state.enable(ExpansionType.VOICE_IO, config, consent_data)
        
        self.assertTrue(state.is_enabled(ExpansionType.VOICE_IO))
        self.assertEqual(state.get_config(ExpansionType.VOICE_IO), config)
        self.assertEqual(len(state.consent_records), 1)
        
        # Check consent record
        record = state.consent_records[0]
        self.assertEqual(record["expansion_type"], ExpansionType.VOICE_IO)
        self.assertEqual(record["action"], "enabled")
        self.assertIn("timestamp", record)
        self.assertEqual(record["hardware_fingerprint"], "test_fingerprint")
    
    def test_disable(self):
        """Test disabling an expansion."""
        state = ExpansionState()
        
        # First enable
        config = {"voice_model": "whisper"}
        consent_data = {"hardware_fingerprint": "test_fingerprint"}
        state.enable(ExpansionType.VOICE_IO, config, consent_data)
        
        # Then disable
        disable_consent = {"hardware_fingerprint": "test_fingerprint"}
        state.disable(ExpansionType.VOICE_IO, disable_consent)
        
        self.assertFalse(state.is_enabled(ExpansionType.VOICE_IO))
        self.assertEqual(len(state.consent_records), 2)  # One enable, one disable
        
        # Check disable record
        disable_record = state.consent_records[1]
        self.assertEqual(disable_record["action"], "disabled")


class TestExpansionStateManager(unittest.TestCase):
    """Test expansion state manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir)
        self.manager = ExpansionStateManager(self.config_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_expansion_state_new(self):
        """Test loading state when no state file exists."""
        state = self.manager.load_expansion_state()
        
        self.assertIsInstance(state, ExpansionState)
        self.assertEqual(len(state.enabled_expansions), 0)
        self.assertEqual(len(state.consent_records), 0)
    
    def test_save_and_load_expansion_state(self):
        """Test saving and loading expansion state."""
        # Create state and enable an expansion
        state = ExpansionState()
        config = {"voice_model": "whisper"}
        consent_data = {"hardware_fingerprint": "test_fingerprint"}
        state.enable(ExpansionType.VOICE_IO, config, consent_data)
        
        # Save state
        self.manager.save_expansion_state(state)
        
        # Load state
        loaded_state = self.manager.load_expansion_state()
        
        self.assertTrue(loaded_state.is_enabled(ExpansionType.VOICE_IO))
        self.assertEqual(loaded_state.get_config(ExpansionType.VOICE_IO), config)
        self.assertEqual(len(loaded_state.consent_records), 1)
    
    def test_is_expansion_enabled(self):
        """Test checking if expansion is enabled."""
        self.assertFalse(self.manager.is_expansion_enabled(ExpansionType.VOICE_IO))
        
        # Enable expansion
        state = self.manager.load_expansion_state()
        state.enable(
            ExpansionType.VOICE_IO,
            {"config": "test"},
            {"hardware_fingerprint": "test"}
        )
        self.manager.save_expansion_state(state)
        
        self.assertTrue(self.manager.is_expansion_enabled(ExpansionType.VOICE_IO))
    
    def test_enable_expansion(self):
        """Test enabling an expansion."""
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        
        self.manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        self.assertTrue(self.manager.is_expansion_enabled(ExpansionType.VOICE_IO))
        loaded_config = self.manager.get_expansion_config(ExpansionType.VOICE_IO)
        self.assertEqual(loaded_config, config)
    
    def test_disable_expansion(self):
        """Test disabling an expansion."""
        # First enable
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        # Then disable
        disable_metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.manager.disable_expansion(ExpansionType.VOICE_IO, disable_metadata)
        
        self.assertFalse(self.manager.is_expansion_enabled(ExpansionType.VOICE_IO))
    
    def test_get_expansion_config(self):
        """Test getting expansion configuration."""
        self.assertIsNone(self.manager.get_expansion_config(ExpansionType.VOICE_IO))
        
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        loaded_config = self.manager.get_expansion_config(ExpansionType.VOICE_IO)
        self.assertEqual(loaded_config, config)
    
    def test_generate_hardware_fingerprint(self):
        """Test hardware fingerprint generation."""
        hardware_dict = {
            "platform": "Darwin",
            "memory_gb": 16.0,
            "cpu_cores": 4
        }
        
        fingerprint = self.manager.generate_hardware_fingerprint(hardware_dict)
        
        self.assertIsInstance(fingerprint, str)
        self.assertGreater(len(fingerprint), 0)
        
        # Same hardware should generate same fingerprint
        fingerprint2 = self.manager.generate_hardware_fingerprint(hardware_dict)
        self.assertEqual(fingerprint, fingerprint2)


if __name__ == "__main__":
    unittest.main()

