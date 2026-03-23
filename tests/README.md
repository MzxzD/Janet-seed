# Test Suite Documentation

Comprehensive test suite for J.A.N.E.T. Seed covering unit tests, integration tests, and testing strategies.

## Purpose

The test suite ensures:
- **Reliability**: All components work as expected
- **Constitutional Compliance**: Axioms are properly enforced
- **Integration**: Components work together correctly
- **Regression Prevention**: Changes don't break existing functionality

## Test Structure

```
tests/
├── __init__.py
├── test_abilities_store.py         # Abilities store / "What can you do?"
├── test_e2e_api.py                 # E2E: API health, models, chat (needs server)
├── test_e2e_ctl.py                 # E2E: Menu bar control surface (--ctl)
├── test_edge_cases.py              # Edge: server down, bad port, install script
├── test_expansion_detector.py      # Expansion detection tests
├── test_expansion_state.py         # State management tests
├── test_expansion_dialog.py        # Suggestion dialogue tests
├── test_wizard_base.py             # Wizard base class tests
├── test_model_manager.py           # Model manager tests
└── test_expansion_integration.py   # End-to-end expansion tests
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **Expansion Detector**: Detection logic, requirements, opportunity creation
- **Expansion State**: Enable/disable, consent records, persistence
- **Expansion Dialog**: Suggestion flows, user interaction
- **Wizard Base**: Base functionality, network checks, offline instructions
- **Model Manager**: Model detection, verification, offline guidance

### E2E and Edge-Case Tests

- **test_e2e_api.py**: Health, `/v1/models`, chat (skipped when server not running).
- **test_e2e_ctl.py**: Menu bar `--ctl` (config-get, config-set, status) — no server required.
- **test_edge_cases.py**: API when server down, bad port, timeout, malformed JSON, wrong API key; install script idempotent and `JANET_SEED_DIR`. Run with the rest of the suite; no live server needed for edge tests.

### Integration Tests

Test component interactions:

- **Expansion Flow**: Detection → suggestion → wizard → enable
- **State Persistence**: Save and load expansion state
- **Consent Records**: Consent storage and retrieval
- **Multi-Expansion**: Multiple expansions enabled simultaneously
- **Hardware Fingerprint**: Consistency across sessions

## Running Tests

Install dependencies first:

```bash
pip install -r requirements.txt
```

### All Tests

```bash
python -m pytest tests/
```

### Specific Test File

```bash
python -m pytest tests/test_expansion_detector.py
```

### With Coverage

```bash
python -m pytest tests/ --cov=src/expansion --cov-report=html
```

## Test Coverage

Current coverage includes:

- ✅ Expansion detector logic
- ✅ State management operations
- ✅ Dialog suggestion flows
- ✅ Wizard base functionality
- ✅ Model manager operations
- ✅ Integration flows

## Writing New Tests

### Unit Test Template

```python
import unittest
from unittest.mock import Mock
from src.expansion import ExpansionDetector

class TestNewComponent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.component = NewComponent()
    
    def test_feature(self):
        """Test specific feature."""
        result = self.component.do_something()
        self.assertEqual(result, expected)
```

### Integration Test Template

```python
import unittest
import tempfile
from pathlib import Path

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_flow(self):
        """Test complete flow."""
        # Test implementation
        pass
```

## Mocking Strategy

Tests use mocks for:
- Hardware profiles (avoid actual hardware detection)
- External services (n8n, Home Assistant)
- File system operations (use temp directories)
- Network operations (mock socket connections)

## Constitutional Testing

Tests verify constitutional compliance:

- **Red Thread**: All operations check Red Thread status
- **Consent**: All expansions require explicit consent
- **Soul Check**: Triggered before major operations
- **Memory Gates**: Memory writes respect gates

## See Also

- [Expansion System](../src/expansion/README.md) - What's being tested
- [Contributing Guide](../documentation/CONTRIBUTING.md) - Testing guidelines

