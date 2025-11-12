# Tamil AI Voice Assistant - Testing Framework

This directory contains a comprehensive testing suite for validating all aspects of the Tamil AI Voice Assistant, including the new database integration and session management features.

## 🧪 Test Suite Overview

### Test Categories

1. **Infrastructure Tests** (`integration/test-infrastructure.py`)
   - PostgreSQL database connectivity and pgVector extension
   - Redis cache operations and session storage
   - MinIO object storage functionality
   - Service integration validation

2. **Unit Tests** (`unit/`)
   - `test_session_service.py` - Database session management testing
   - Individual component validation
   - Isolated functionality verification

3. **Integration Tests** (`integration/test_end_to_end.py`)
   - Complete workflow validation
   - API endpoint testing
   - WebSocket communication
   - Document upload and processing
   - Chat conversation flows
   - Speech component integration

4. **Performance Tests** (`performance/`)
   - API response time benchmarking
   - Throughput testing
   - Resource utilization monitoring

## 🚀 Quick Start

### Prerequisites

Ensure the development environment is running:

```bash
# Start infrastructure services
docker compose -f docker-compose.dev.yml up -d

# Start backend
source .venv/bin/activate
python -m uvicorn backend.main:app --reload

# Verify services
curl http://localhost:8000/health
```

### Running Tests

#### Option 1: Run All Tests (Recommended)
```bash
# Run complete test suite
python tests/run_all_tests.py

# Run with detailed output
python tests/run_all_tests.py --verbose
```

#### Option 2: Run Specific Test Categories
```bash
# Infrastructure tests only
python tests/integration/test-infrastructure.py

# End-to-end integration tests
python tests/integration/test_end_to_end.py

# Unit tests only
python tests/run_all_tests.py --unit-only

# Quick tests (infrastructure + integration)
python tests/run_all_tests.py --quick
```

#### Option 3: Individual Test Execution
```bash
# Session service unit tests
python tests/unit/test_session_service.py

# Individual component tests
python tests/utils/demo-rag-qa.py
python tests/utils/test-noise-reduction.py
```

## 📊 Test Results Interpretation

### Exit Codes
- **0**: All tests passed (≥80% pass rate)
- **1**: Some tests failed (60-79% pass rate)
- **2**: Major failures (<60% pass rate)

### Pass Rate Guidelines
- **100%**: Production ready ✅
- **80-99%**: Good, minor issues to address ⚠️
- **60-79%**: Fair, significant issues need attention ⚠️
- **<60%**: Poor, major debugging required ❌

## 🔧 Test Configuration

### Environment Variables
Tests automatically detect environment configuration from `.env` file and Docker settings.

### Test Data
- Tests use temporary data that is cleaned up automatically
- No persistent test data affects production databases
- Session tests use isolated user IDs (e.g., `test_user_integration`)

### Timeouts
- Individual tests: 5 minutes
- WebSocket tests: 10 seconds
- API tests: 30 seconds

## 📁 Test Directory Structure

```
tests/
├── README.md                     # This file
├── run_all_tests.py              # Comprehensive test runner
├── integration/                  # Integration tests
│   ├── test-infrastructure.py    # Service connectivity tests
│   ├── test_end_to_end.py        # End-to-end workflow tests
│   └── test_docker_services.py   # Docker environment tests
├── unit/                         # Unit tests
│   ├── test_session_service.py   # Database session management tests
│   └── test_*.py                 # Additional component tests
├── performance/                  # Performance benchmarks
│   └── test_basic_performance.py # Basic API performance tests
├── utils/                        # Utility tests and demos
│   ├── demo-rag-qa.py           # RAG pipeline demonstration
│   ├── test-noise-reduction.py  # Audio processing tests
│   └── query-rag.py             # RAG query testing
└── data/                        # Test fixtures and sample data
```

## 🐛 Troubleshooting

### Common Issues

#### Backend Not Running
```bash
Error: Backend not accessible
Solution: Start backend with: python -m uvicorn backend.main:app --reload
```

#### Docker Services Down
```bash
Error: PostgreSQL/Redis/MinIO connection failed
Solution: docker compose -f docker-compose.dev.yml up -d
```

#### Import Errors
```bash
Error: Module not found
Solution: Ensure virtual environment is activated and dependencies installed
pip install -r requirements.txt
```

#### Permission Errors
```bash
Error: Permission denied
Solution: Check file permissions and ensure proper Docker volume mounts
```

### Database Issues

#### Migration Problems
```bash
# Reset database schema
python -c "from database.connection import reset_database; import asyncio; asyncio.run(reset_database())"

# Re-run migrations
python -m alembic upgrade head
```

#### Session Cache Issues
```bash
# Clear Redis cache
docker exec tamil-assistant-redis redis-cli FLUSHALL
```

### Test-Specific Debugging

#### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Run Tests with Debug Output
```bash
python -c "import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())" tests/run_all_tests.py
```

#### Individual Component Testing
```bash
# Test database session management directly
python -c "
import asyncio
from tests.unit.test_session_service import run_manual_tests
asyncio.run(run_manual_tests())
"
```

## 📈 Performance Benchmarks

### Expected Performance Metrics

| Component | Expected Response Time | Threshold |
|-----------|----------------------|-----------|
| Health Check | <100ms | 200ms |
| Session Creation | <300ms | 500ms |
| Document Upload | <2s | 5s |
| Chat API | <1s | 3s |
| TTS Generation | <2s | 5s |
| RAG Retrieval | <500ms | 1s |

### Performance Test Commands
```bash
# Basic performance tests
python tests/performance/test_basic_performance.py

# Comprehensive benchmarking
python tests/run_all_tests.py --performance-only
```

## 🔄 Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: |
          docker compose -f docker-compose.dev.yml up -d
          python tests/run_all_tests.py --no-performance
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Add to .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run test suite
        entry: python tests/run_all_tests.py --quick
        language: python
```

## 📚 Additional Resources

- [Infrastructure Setup Guide](../docs/setup/docker-setup.md)
- [API Documentation](../docs/api/README.md)
- [Troubleshooting Guide](../docs/troubleshooting/common-issues.md)
- [Development Guidelines](../docs/development/README.md)

## 🤝 Contributing

When adding new tests:

1. **Unit Tests**: Add to `unit/test_[component].py`
2. **Integration Tests**: Add to `integration/test_[workflow].py`
3. **Performance Tests**: Add to `performance/test_[benchmark].py`
4. **Update Documentation**: Update this README with new test descriptions

### Test Writing Guidelines

1. **Use descriptive test names**: `test_session_creation_with_metadata()`
2. **Include setup/teardown**: Clean up test data
3. **Add error cases**: Test both success and failure scenarios
4. **Document expected behavior**: Add docstrings explaining test purpose
5. **Use fixtures**: Create reusable test data and components

### Example Test Structure
```python
@pytest.mark.asyncio
async def test_feature_functionality():
    """Test that feature works correctly with valid input."""
    # Arrange
    test_data = create_test_data()

    # Act
    result = await feature_function(test_data)

    # Assert
    assert result is not None
    assert result.status == "success"

    # Cleanup
    await cleanup_test_data(test_data.id)
```

---

*For technical support, see the [main project documentation](../README.md) or [troubleshooting guide](../docs/troubleshooting/).*