# Chaotic AF Test Suite

## Test Results: 71/71 Passing ✅

## Structure

- `unit/` - Unit tests for individual components (54 tests)
  - `test_control_socket.py` - Tests for the Unix socket control mechanism
  - `test_socket_client.py` - Tests for the centralized AgentSocketClient
  - `test_agent_config.py` - Configuration handling tests
  - `test_cli_connect.py` - CLI connection command tests
  - `test_connection_manager.py` - Dynamic connection management tests
  - `test_llm_provider.py` - LLM abstraction layer tests
  - `test_mcp_client.py` - MCP client implementation tests
  - `test_supervisor.py` - Process supervisor tests
  
- `integration/` - Integration tests for full system behavior (17 tests)
  - `test_socket_mode.py` - Tests for socket mode with real agents
  - `test_full_flow.py` - Complete agent-to-agent communication flows
  - `test_graceful_shutdown.py` - Shutdown sequence verification
  - `test_health_monitoring.py` - Auto-recovery and health check tests
  - `test_metrics_collection.py` - Prometheus metrics tests
  - `test_cli_enhancements.py` - CLI command functionality tests
  - `test_three_bot_discussion.py` - Multi-agent conversation tests

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
pytest tests/unit/test_socket_client.py
pytest tests/integration/test_health_monitoring.py
```

## Key Features Tested

### Core Functionality
- ✅ Zero-CPU socket communication
- ✅ Agent lifecycle management
- ✅ Dynamic agent connections
- ✅ MCP protocol integration
- ✅ Event streaming and subscription

### Advanced Features  
- ✅ Health monitoring and auto-recovery
- ✅ Graceful shutdown sequences
- ✅ Prometheus metrics collection
- ✅ CLI command functionality
- ✅ Interactive chat event handling

### Reliability
- ✅ Process isolation and crash handling
- ✅ Socket connection resilience
- ✅ Race condition prevention
- ✅ Resource cleanup verification
