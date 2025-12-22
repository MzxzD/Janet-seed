"""
Unit tests for Expansion Detector
"""
import unittest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expansion.expansion_detector import ExpansionDetector
from expansion.expansion_types import ExpansionType, ExpansionOpportunity
from hardware_detector import HardwareProfile


class TestExpansionDetector(unittest.TestCase):
    """Test expansion detection logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock hardware profile
        self.hardware = Mock(spec=HardwareProfile)
        self.hardware.memory_gb = 16.0
        self.hardware.disk_free_gb = 50.0
        self.hardware.cpu_cores_physical = 4
        self.hardware.can_run_feature = Mock(return_value=True)
        
        # Create detector with empty current state
        self.detector = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state={}
        )
    
    def test_detect_available_expansions_empty_state(self):
        """Test detection when no expansions are enabled."""
        opportunities = self.detector.detect_available_expansions()
        
        # Should detect multiple opportunities
        self.assertIsInstance(opportunities, list)
        self.assertGreater(len(opportunities), 0)
        
        # Check that opportunities are ExpansionOpportunity objects
        for opp in opportunities:
            self.assertIsInstance(opp, ExpansionOpportunity)
            self.assertIn(opp.expansion_type, [
                ExpansionType.VOICE_IO,
                ExpansionType.PERSISTENT_MEMORY,
                ExpansionType.DELEGATION,
                ExpansionType.MODEL_INSTALLATION,
                ExpansionType.N8N_INTEGRATION,
                ExpansionType.HOME_ASSISTANT_INTEGRATION,
            ])
    
    def test_detect_available_expansions_with_enabled_features(self):
        """Test detection when some features are already enabled."""
        # Set up detector with voice already enabled
        detector = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state={"voice_io_enabled": True}
        )
        
        opportunities = detector.detect_available_expansions()
        
        # Voice I/O should not be in opportunities
        voice_opportunities = [o for o in opportunities if o.expansion_type == ExpansionType.VOICE_IO]
        self.assertEqual(len(voice_opportunities), 0)
    
    def test_can_expand_to_voice_io(self):
        """Test voice I/O expansion check."""
        # With sufficient hardware and not enabled
        self.hardware.can_run_feature.return_value = True
        result = self.detector.can_expand_to(ExpansionType.VOICE_IO)
        self.assertTrue(result)
        
        # When already enabled
        detector_enabled = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state={"voice_io_enabled": True}
        )
        result = detector_enabled.can_expand_to(ExpansionType.VOICE_IO)
        self.assertFalse(result)
    
    def test_can_expand_to_memory(self):
        """Test persistent memory expansion check."""
        # With sufficient hardware and not enabled
        self.hardware.can_run_feature.return_value = True
        result = self.detector.can_expand_to(ExpansionType.PERSISTENT_MEMORY)
        self.assertTrue(result)
        
        # When already enabled
        detector_enabled = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state={"memory_enabled": True}
        )
        result = detector_enabled.can_expand_to(ExpansionType.PERSISTENT_MEMORY)
        self.assertFalse(result)
    
    def test_can_expand_to_delegation(self):
        """Test delegation expansion check."""
        # With sufficient hardware and not enabled
        self.hardware.can_run_feature.return_value = True
        result = self.detector.can_expand_to(ExpansionType.DELEGATION)
        self.assertTrue(result)
        
        # When already enabled
        detector_enabled = ExpansionDetector(
            hardware_profile=self.hardware,
            current_state={"delegation_enabled": True}
        )
        result = detector_enabled.can_expand_to(ExpansionType.DELEGATION)
        self.assertFalse(result)
    
    def test_can_expand_to_models(self):
        """Test model installation expansion check."""
        # With sufficient hardware (8GB RAM, 10GB disk)
        self.hardware.memory_gb = 16.0
        self.hardware.disk_free_gb = 50.0
        result = self.detector.can_expand_to(ExpansionType.MODEL_INSTALLATION)
        self.assertTrue(result)
        
        # With insufficient memory
        self.hardware.memory_gb = 4.0
        result = self.detector.can_expand_to(ExpansionType.MODEL_INSTALLATION)
        self.assertFalse(result)
    
    def test_get_expansion_requirements(self):
        """Test getting expansion requirements."""
        # Voice I/O requirements
        reqs = self.detector.get_expansion_requirements(ExpansionType.VOICE_IO)
        self.assertIn("memory_gb", reqs)
        self.assertIn("disk_gb", reqs)
        self.assertIn("microphone", reqs)
        self.assertIn("speaker", reqs)
        
        # Memory requirements
        reqs = self.detector.get_expansion_requirements(ExpansionType.PERSISTENT_MEMORY)
        self.assertIn("memory_gb", reqs)
        self.assertIn("disk_gb", reqs)
        
        # Unknown expansion type
        reqs = self.detector.get_expansion_requirements("unknown_type")
        self.assertEqual(reqs, {})
    
    def test_create_voice_io_opportunity(self):
        """Test voice I/O opportunity creation."""
        opportunity = self.detector._create_voice_io_opportunity()
        
        self.assertEqual(opportunity.expansion_type, ExpansionType.VOICE_IO)
        self.assertEqual(opportunity.name, "Voice Input/Output")
        self.assertGreater(len(opportunity.benefits), 0)
        self.assertGreater(len(opportunity.risks), 0)
        self.assertTrue(opportunity.reversible)
        self.assertFalse(opportunity.requires_network)
    
    def test_create_memory_opportunity(self):
        """Test persistent memory opportunity creation."""
        opportunity = self.detector._create_memory_opportunity()
        
        self.assertEqual(opportunity.expansion_type, ExpansionType.PERSISTENT_MEMORY)
        self.assertEqual(opportunity.name, "Persistent Memory")
        self.assertGreater(len(opportunity.benefits), 0)
        self.assertTrue(opportunity.reversible)
        self.assertFalse(opportunity.requires_network)
    
    def test_create_delegation_opportunity(self):
        """Test delegation opportunity creation."""
        opportunity = self.detector._create_delegation_opportunity()
        
        self.assertEqual(opportunity.expansion_type, ExpansionType.DELEGATION)
        self.assertEqual(opportunity.name, "Task Delegation")
        self.assertGreater(len(opportunity.benefits), 0)
        self.assertTrue(opportunity.reversible)


if __name__ == "__main__":
    unittest.main()

