"""
Unit tests for Wizard Base
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expansion.wizards.wizard_base import ExpansionWizard


class TestExpansionWizard(unittest.TestCase):
    """Test expansion wizard base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir)
        self.janet_core = Mock()
        
        # Create a concrete wizard instance for testing
        self.wizard = ExpansionWizard(self.config_path, self.janet_core)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test wizard initialization."""
        self.assertEqual(self.wizard.config_path, self.config_path)
        self.assertEqual(self.wizard.janet_core, self.janet_core)
        self.assertIsNone(self.wizard.config)
    
    def test_validate_requirements_base(self):
        """Test base validate_requirements method."""
        # Base class should return (True, [])
        valid, missing = self.wizard.validate_requirements()
        
        self.assertTrue(valid)
        self.assertEqual(missing, [])
    
    def test_setup_base(self):
        """Test base setup method."""
        # Base class should return False (not implemented)
        result = self.wizard.setup()
        
        self.assertFalse(result)
    
    def test_verify_base(self):
        """Test base verify method."""
        # Base class should return False (not implemented)
        result = self.wizard.verify()
        
        self.assertFalse(result)
    
    def test_cleanup_on_failure(self):
        """Test cleanup on failure."""
        # Should not raise exception
        try:
            self.wizard.cleanup_on_failure()
        except Exception as e:
            self.fail(f"cleanup_on_failure raised {e}")
    
    @patch('socket.create_connection')
    def test_check_network_available_online(self, mock_socket):
        """Test network check when online."""
        mock_socket.return_value = True
        
        result = self.wizard.check_network_available()
        
        self.assertTrue(result)
    
    @patch('socket.create_connection')
    def test_check_network_available_offline(self, mock_socket):
        """Test network check when offline."""
        import socket
        mock_socket.side_effect = socket.error("No network")
        
        result = self.wizard.check_network_available()
        
        self.assertFalse(result)
    
    def test_generate_offline_instructions_base(self):
        """Test base offline instructions generation."""
        # Base class should return empty string
        instructions = self.wizard.generate_offline_instructions()
        
        self.assertEqual(instructions, "")
    
    def test_run_base(self):
        """Test base run method."""
        # Base class should return False (not implemented)
        result = self.wizard.run()
        
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

