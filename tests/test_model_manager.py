"""
Unit tests for Model Manager
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import sys
import subprocess
import platform

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from expansion.model_manager import ModelManager


class TestModelManager(unittest.TestCase):
    """Test model manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ModelManager()
    
    @patch('shutil.which')
    def test_find_ollama_path_found(self, mock_which):
        """Test finding Ollama path when available."""
        mock_which.return_value = "/usr/bin/ollama"
        
        manager = ModelManager()
        
        self.assertIsNotNone(manager.ollama_path)
        self.assertEqual(str(manager.ollama_path), "/usr/bin/ollama")
    
    @patch('shutil.which')
    def test_find_ollama_path_not_found(self, mock_which):
        """Test finding Ollama path when not available."""
        mock_which.return_value = None
        
        manager = ModelManager()
        
        self.assertIsNone(manager.ollama_path)
    
    @patch('subprocess.run')
    def test_verify_ollama_model_exists(self, mock_run):
        """Test verifying model when it exists."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="NAME                SIZE\n tinyllama:1.1b      2.3GB\n"
        )
        self.manager.ollama_path = Path("/usr/bin/ollama")
        
        result = self.manager.verify_ollama_model("tinyllama:1.1b")
        
        self.assertTrue(result)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_verify_ollama_model_not_exists(self, mock_run):
        """Test verifying model when it doesn't exist."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="NAME                SIZE\n"
        )
        self.manager.ollama_path = Path("/usr/bin/ollama")
        
        result = self.manager.verify_ollama_model("deepseek-coder:6.7b")
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_list_available_models(self, mock_run):
        """Test listing available models."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="NAME                SIZE\n tinyllama:1.1b      2.3GB\n deepseek-coder:6.7b  4.1GB\n"
        )
        self.manager.ollama_path = Path("/usr/bin/ollama")
        
        models = self.manager.list_available_models()
        
        self.assertIn("tinyllama:1.1b", models)
        self.assertIn("deepseek-coder:6.7b", models)
    
    @patch('subprocess.run')
    def test_list_available_models_no_ollama(self, mock_run):
        """Test listing models when Ollama not available."""
        self.manager.ollama_path = None
        
        models = self.manager.list_available_models()
        
        self.assertEqual(models, [])
        mock_run.assert_not_called()
    
    def test_detect_missing_models(self):
        """Test detecting missing models."""
        # Mock available models
        with patch.object(self.manager, 'list_available_models', return_value=["tinyllama:1.1b"]):
            required = ["tinyllama:1.1b", "deepseek-coder:6.7b"]
            missing = self.manager.detect_missing_models(required)
            
            self.assertIn("deepseek-coder:6.7b", missing)
            self.assertNotIn("tinyllama:1.1b", missing)
    
    @patch('platform.system')
    def test_get_ollama_model_path_macos(self, mock_system):
        """Test getting model path on macOS."""
        mock_system.return_value = "Darwin"
        
        path = self.manager.get_ollama_model_path()
        
        self.assertIn(".ollama", str(path))
        self.assertIn("models", str(path))
    
    @patch('platform.system')
    def test_get_ollama_model_path_linux(self, mock_system):
        """Test getting model path on Linux."""
        mock_system.return_value = "Linux"
        
        path = self.manager.get_ollama_model_path()
        
        self.assertIn(".ollama", str(path))
        self.assertIn("models", str(path))
    
    @patch('platform.system')
    def test_get_ollama_model_path_windows(self, mock_system):
        """Test getting model path on Windows."""
        mock_system.return_value = "Windows"
        
        path = self.manager.get_ollama_model_path()
        
        self.assertIn(".ollama", str(path))
        self.assertIn("models", str(path))
    
    @patch('socket.create_connection')
    def test_check_network_available_online(self, mock_socket):
        """Test network check when online."""
        mock_socket.return_value = True
        
        result = self.manager.check_network_available()
        
        self.assertTrue(result)
    
    @patch('socket.create_connection')
    def test_check_network_available_offline(self, mock_socket):
        """Test network check when offline."""
        import socket
        mock_socket.side_effect = socket.error("No network")
        
        result = self.manager.check_network_available()
        
        self.assertFalse(result)
    
    @patch('platform.system')
    def test_generate_offline_installation_instructions(self, mock_system):
        """Test generating offline installation instructions."""
        mock_system.return_value = "Darwin"
        
        instructions = self.manager.generate_offline_installation_instructions("deepseek-coder:6.7b")
        
        self.assertIn("deepseek-coder:6.7b", instructions)
        self.assertIn("STEP 1", instructions)
        self.assertIn("STEP 2", instructions)
        self.assertIn("STEP 3", instructions)
        self.assertIn("STEP 4", instructions)
        self.assertIn("STEP 5", instructions)
        self.assertIn("TROUBLESHOOTING", instructions)
    
    @patch('subprocess.run')
    def test_verify_model_installation_success(self, mock_run):
        """Test verifying model installation when successful."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="NAME                SIZE\n deepseek-coder:6.7b  4.1GB\n"
        )
        self.manager.ollama_path = Path("/usr/bin/ollama")
        
        # Mock verify_ollama_model to return True
        with patch.object(self.manager, 'verify_ollama_model', return_value=True):
            success, message = self.manager.verify_model_installation("deepseek-coder:6.7b")
            
            self.assertTrue(success)
            self.assertIn("verified", message.lower())
    
    def test_verify_model_installation_no_ollama(self):
        """Test verifying model when Ollama not available."""
        self.manager.ollama_path = None
        
        success, message = self.manager.verify_model_installation("deepseek-coder:6.7b")
        
        self.assertFalse(success)
        self.assertIn("Ollama not found", message)
    
    def test_get_learning_capable_models(self):
        """Test getting learning-capable models."""
        models = self.manager.get_learning_capable_models()
        
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        self.assertIn("tinyllama:1.1b", models)


if __name__ == "__main__":
    unittest.main()

