# Chaotic AF Test Suite

## Structure

- `unit/` - Unit tests for individual components
  - `test_control_socket.py` - Tests for the Unix socket control mechanism
  
- `integration/` - Integration tests for full system behavior
  - `test_socket_mode.py` - Tests for socket mode with real agents

## Running Tests

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

Run all tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=agent_framework --cov-report=html
```

Run specific test:
```bash
pytest tests/unit/test_control_socket.py
```

## Key Test: CPU Fix Verification

The most important test verifies that socket mode fixes the CPU usage issue:
```bash
python tests/test_cpu_fix.py
```

This should show CPU usage < 5% (typically 0.1-0.5%) instead of 80-100%.
