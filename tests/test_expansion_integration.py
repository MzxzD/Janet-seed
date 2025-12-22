"""
Integration tests for Expansion Protocol
Tests end-to-end expansion flows including consent, enable/disable, and failure handling.
"""
import unittest
import tempfile
import json
from pathlib import Path
import sys
from unittest.mock import Mock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expansion.expansion_detector import ExpansionDetector
from expansion.expansion_state import ExpansionStateManager
from expansion.expansion_dialog import ExpansionDialog
from expansion.expansion_types import ExpansionType, ExpansionOpportunity
from expansion.model_manager import ModelManager
from hardware_detector import HardwareProfile


class TestExpansionIntegration(unittest.TestCase):
    """Integration tests for expansion protocol."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir)
        
        # Create mock hardware profile
        self.hardware = Mock(spec=HardwareProfile)
        self.hardware.memory_gb = 16.0
        self.hardware.disk_free_gb = 50.0
        self.hardware.cpu_cores_physical = 4
        self.hardware.can_run_feature = Mock(return_value=True)
        
        # Initialize components
        self.state_manager = ExpansionStateManager(self.config_path)
        self.detector = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state={}
        )
        self.janet_core = Mock()
        self.dialog = ExpansionDialog(janet_core=self.janet_core)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_expansion_flow_detection_to_enable(self):
        """Test complete flow from detection to enabling expansion."""
        # Step 1: Detect opportunities
        opportunities = self.detector.detect_available_expansions()
        self.assertGreater(len(opportunities), 0)
        
        # Step 2: Get voice I/O opportunity
        voice_opp = next(
            (o for o in opportunities if o.expansion_type == ExpansionType.VOICE_IO),
            None
        )
        self.assertIsNotNone(voice_opp)
        
        # Step 3: Enable expansion
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        # Step 4: Verify expansion is enabled
        self.assertTrue(self.state_manager.is_expansion_enabled(ExpansionType.VOICE_IO))
        loaded_config = self.state_manager.get_expansion_config(ExpansionType.VOICE_IO)
        self.assertEqual(loaded_config, config)
        
        # Step 5: Verify state persists
        new_state_manager = ExpansionStateManager(self.config_path)
        self.assertTrue(new_state_manager.is_expansion_enabled(ExpansionType.VOICE_IO))
    
    def test_expansion_flow_enable_disable_cycle(self):
        """Test enabling and disabling an expansion."""
        # Enable
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        self.assertTrue(self.state_manager.is_expansion_enabled(ExpansionType.VOICE_IO))
        
        # Disable
        disable_metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.disable_expansion(ExpansionType.VOICE_IO, disable_metadata)
        self.assertFalse(self.state_manager.is_expansion_enabled(ExpansionType.VOICE_IO))
        
        # Verify consent records
        state = self.state_manager.load_expansion_state()
        self.assertEqual(len(state.consent_records), 2)  # One enable, one disable
    
    def test_expansion_detection_with_enabled_features(self):
        """Test that detector doesn't suggest already-enabled features."""
        # Enable voice I/O
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        # Create detector with updated state
        current_state = {
            "voice_io_enabled": True,
            "memory_enabled": False,
            "delegation_enabled": False,
        }
        detector = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state=current_state
        )
        
        # Detect opportunities
        opportunities = detector.detect_available_expansions()
        
        # Voice I/O should not be in opportunities
        voice_opportunities = [
            o for o in opportunities 
            if o.expansion_type == ExpansionType.VOICE_IO
        ]
        self.assertEqual(len(voice_opportunities), 0)
        
        # Other opportunities should still be available
        self.assertGreater(len(opportunities), 0)
    
    def test_multiple_expansions_enabled(self):
        """Test enabling multiple expansions."""
        # Enable voice I/O
        voice_config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.enable_expansion(ExpansionType.VOICE_IO, voice_config, metadata)
        
        # Enable memory
        memory_config = {"memory_dir": str(self.config_path / "memory")}
        self.state_manager.enable_expansion(
            ExpansionType.PERSISTENT_MEMORY,
            memory_config,
            metadata
        )
        
        # Verify both are enabled
        self.assertTrue(self.state_manager.is_expansion_enabled(ExpansionType.VOICE_IO))
        self.assertTrue(
            self.state_manager.is_expansion_enabled(ExpansionType.PERSISTENT_MEMORY)
        )
        
        # Verify configs are separate
        self.assertEqual(
            self.state_manager.get_expansion_config(ExpansionType.VOICE_IO),
            voice_config
        )
        self.assertEqual(
            self.state_manager.get_expansion_config(ExpansionType.PERSISTENT_MEMORY),
            memory_config
        )
    
    def test_consent_records_persistence(self):
        """Test that consent records persist across sessions."""
        # Enable expansion
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        # Disable expansion
        disable_metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.disable_expansion(ExpansionType.VOICE_IO, disable_metadata)
        
        # Load state in new manager
        new_state_manager = ExpansionStateManager(self.config_path)
        state = new_state_manager.load_expansion_state()
        
        # Verify consent records
        self.assertEqual(len(state.consent_records), 2)
        self.assertEqual(state.consent_records[0]["action"], "enabled")
        self.assertEqual(state.consent_records[1]["action"], "disabled")
        self.assertIn("timestamp", state.consent_records[0])
        self.assertIn("timestamp", state.consent_records[1])
    
    def test_hardware_fingerprint_consistency(self):
        """Test hardware fingerprint generation consistency."""
        hardware_dict = {
            "platform": "Darwin",
            "memory_gb": 16.0,
            "cpu_cores": 4
        }
        
        fingerprint1 = self.state_manager.generate_hardware_fingerprint(hardware_dict)
        fingerprint2 = self.state_manager.generate_hardware_fingerprint(hardware_dict)
        
        # Same hardware should generate same fingerprint
        self.assertEqual(fingerprint1, fingerprint2)
        
        # Different hardware should generate different fingerprint
        hardware_dict2 = {
            "platform": "Linux",
            "memory_gb": 8.0,
            "cpu_cores": 2
        }
        fingerprint3 = self.state_manager.generate_hardware_fingerprint(hardware_dict2)
        self.assertNotEqual(fingerprint1, fingerprint3)
    
    @patch('builtins.input', return_value='yes')
    def test_expansion_dialog_suggestion_flow(self, mock_input):
        """Test expansion dialog suggestion flow."""
        opportunity = ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice I/O",
            description="Enable voice interaction",
            benefits=["Hands-free interaction"],
            risks=["Requires microphone"],
        )
        
        # Suggest expansion
        result = self.dialog.suggest_expansion(opportunity)
        
        # Should return True if user accepts
        self.assertTrue(result)
    
    def test_model_manager_integration(self):
        """Test model manager integration with expansion system."""
        model_manager = ModelManager()
        
        # Test offline installation instructions generation
        instructions = model_manager.generate_offline_installation_instructions(
            "deepseek-coder:6.7b"
        )
        
        self.assertIn("deepseek-coder:6.7b", instructions)
        self.assertIn("STEP 1", instructions)
        self.assertIn("STEP 5", instructions)
        
        # Test learning-capable models
        learning_models = model_manager.get_learning_capable_models()
        self.assertIsInstance(learning_models, list)
        self.assertGreater(len(learning_models), 0)
    
    def test_expansion_requirements_validation(self):
        """Test expansion requirements validation."""
        # Get requirements for different expansion types
        voice_reqs = self.detector.get_expansion_requirements(ExpansionType.VOICE_IO)
        self.assertIn("memory_gb", voice_reqs)
        self.assertIn("microphone", voice_reqs)
        
        memory_reqs = self.detector.get_expansion_requirements(
            ExpansionType.PERSISTENT_MEMORY
        )
        self.assertIn("memory_gb", memory_reqs)
        self.assertIn("disk_gb", memory_reqs)
        
        delegation_reqs = self.detector.get_expansion_requirements(
            ExpansionType.DELEGATION
        )
        self.assertIn("memory_gb", delegation_reqs)
    
    def test_expansion_state_file_persistence(self):
        """Test that expansion state is properly saved to file."""
        # Enable expansion
        config = {"voice_model": "whisper"}
        metadata = {"hardware_fingerprint": "test_fingerprint"}
        self.state_manager.enable_expansion(ExpansionType.VOICE_IO, config, metadata)
        
        # Check that state file exists
        state_file = self.config_path / "expansion_state.json"
        self.assertTrue(state_file.exists())
        
        # Verify file contents
        with open(state_file, 'r') as f:
            data = json.load(f)
            self.assertIn(ExpansionType.VOICE_IO, data.get("enabled_expansions", {}))
            self.assertGreater(len(data.get("consent_records", [])), 0)


if __name__ == "__main__":
    unittest.main()

