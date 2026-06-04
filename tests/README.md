# Test Framework Documentation

## Overview

This test framework provides comprehensive unit and integration tests for the Nexknit Gateway collectors.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── mocks/                   # Mock utilities
│   ├── __init__.py
│   ├── mock_socket.py       # Mock socket for TCP testing
│   ├── mock_process.py      # Mock subprocess for GPU testing
│   └── mock_psutil.py       # Mock psutil for system testing
├── unit/                    # Unit tests
│   ├── test_base_collector.py
│   ├── test_storage_collector.py
│   ├── test_http_alive.py
│   ├── test_gpu.py
│   ├── test_system.py
│   └── test_local_storage.py
└── integration/             # Integration tests
    ├── test_collector_integration.py
    └── test_gateway_integration.py
```

## Requirements

```bash
pip install pytest psutil
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run unit tests only
```bash
pytest tests/unit/ -v
```

### Run integration tests only
```bash
pytest tests/integration/ -v
```

### Run specific test
```bash
pytest tests/unit/test_http_alive.py -v
```

### Run tests with coverage
```bash
pytest tests/ -v --cov=collectors
```

## Test Coverage

### Unit Tests
- **BaseCollector**: Protocol parsing, alert system, TCP sending
- **StorageCollector**: Local storage, caching, history management
- **HttpAliveCollector**: URL checking, multithreading, error handling
- **GPUCollector**: GPU detection, process monitoring
- **SystemCollector**: System metrics collection
- **LocalStorageCollector**: Storage integration

### Integration Tests
- Collector concurrent execution
- Gateway-collector communication
- TCP message sending
- Module imports and inheritance

## Mock Utilities

### MockSocket
Mock socket module for testing TCP communications.

### MockProcess
Mock subprocess module with predefined nvidia-smi outputs.

### MockPsutil
Mock psutil module with configurable system metrics.

## Configuration

### conftest.py
- `mock_server`: Creates a mock TCP server for testing
- `mock_nvidia_smi`: Mock nvidia-smi output
- `mock_psutil`: Mock psutil module
- `alert_config`: Default alert configuration

## Writing New Tests

1. Create new test file in `tests/unit/` or `tests/integration/`
2. Use existing fixtures from `conftest.py`
3. Use mock utilities from `tests/mocks/`
4. Follow pytest conventions

## Notes

- Integration tests may require network access for HTTP tests
- GPU tests require NVIDIA drivers and nvidia-smi for full functionality
- Tests should be isolated and idempotent
