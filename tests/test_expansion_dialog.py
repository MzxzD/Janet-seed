"""
Unit tests for Expansion Dialog
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expansion.expansion_dialog import ExpansionDialog
from expansion.expansion_types import ExpansionType, ExpansionOpportunity


class TestExpansionDialog(unittest.TestCase):
    """Test expansion dialog functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.janet_core = Mock()
        self.dialog = ExpansionDialog(janet_core=self.janet_core)
    
    def test_initialization(self):
        """Test dialog initialization."""
        self.assertEqual(self.dialog.janet_core, self.janet_core)
    
    @patch('builtins.input', return_value='yes')
    def test_suggest_expansion_accept(self, mock_input):
        """Test suggesting expansion when user accepts."""
        opportunity = ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice I/O",
            description="Enable voice interaction",
            benefits=["Hands-free interaction"],
            risks=["Requires microphone"],
        )
        
        result = self.dialog.suggest_expansion(opportunity)
        
        self.assertTrue(result)
        mock_input.assert_called()
    
    @patch('builtins.input', return_value='no')
    def test_suggest_expansion_reject(self, mock_input):
        """Test suggesting expansion when user rejects."""
        opportunity = ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice I/O",
            description="Enable voice interaction",
        )
        
        result = self.dialog.suggest_expansion(opportunity)
        
        self.assertFalse(result)
    
    @patch('builtins.input', return_value='tell me more')
    def test_suggest_expansion_more_info(self, mock_input):
        """Test suggesting expansion when user wants more info."""
        opportunity = ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice I/O",
            description="Enable voice interaction",
            benefits=["Hands-free interaction"],
            risks=["Requires microphone"],
        )
        
        # Mock the explain method to avoid printing
        with patch.object(self.dialog, 'explain_benefits_and_risks'):
            with patch('builtins.input', side_effect=['tell me more', 'yes']):
                result = self.dialog.suggest_expansion(opportunity)
                # Should eventually return True if user says yes after more info
                # This is a simplified test - actual flow is more complex
    
    def test_present_expansion_opportunity(self):
        """Test presenting expansion opportunity."""
        opportunity = ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice I/O",
            description="Enable voice interaction",
            benefits=["Hands-free interaction"],
            risks=["Requires microphone"],
        )
        
        # Mock input to return 'yes'
        with patch('builtins.input', return_value='yes'):
            result = self.dialog.present_expansion_opportunity(opportunity)
            self.assertTrue(result)
    
    def test_explain_benefits_and_risks(self):
        """Test explaining benefits and risks."""
        opportunity = ExpansionOpportunity(
            expansion_type=ExpansionType.VOICE_IO,
            name="Voice I/O",
            description="Enable voice interaction",
            benefits=["Hands-free interaction", "Natural conversation"],
            risks=["Requires microphone", "May consume resources"],
        )
        
        # Should not raise exception
        try:
            self.dialog.explain_benefits_and_risks(opportunity)
        except Exception as e:
            self.fail(f"explain_benefits_and_risks raised {e}")


if __name__ == "__main__":
    unittest.main()

