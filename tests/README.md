# Tests Directory

This directory contains all test files for the Agent Monitor project.

## Test Files

### `test_telemetry.py`
Comprehensive integration test for the telemetry system. Tests:
- Dependency injection container initialization
- Database connectivity and operations  
- Event recording and retrieval
- Statistics generation
- Analytics report generation
- Detection accuracy trends

### `test_quickstart.py`
Demonstration test that follows the quickstart workflow. Tests:
- Basic telemetry system setup
- Standard detection event recording
- Custom event recording with metadata
- Analytics functionality
- Real-time statistics

## Running Tests

### Run All Tests
```bash
# From project root directory
./run_tests.sh
```

### Run Individual Tests
```bash
# Run telemetry tests
python tests/test_telemetry.py

# Run quickstart tests  
python tests/test_quickstart.py
```

### Prerequisites
- Virtual environment must be activated: `source venv/bin/activate`
- All dependencies installed: `pip install -r requirements.txt`
- Telemetry system database initialized (happens automatically on first run)

## Test Structure

The tests are organized to:
- Import project modules using relative paths
- Test both individual components and full integration
- Provide clear output and error reporting
- Validate both functionality and data integrity

## Adding New Tests

When adding new test files:
1. Place them in this `tests/` directory
2. Add the parent directory to Python path:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   ```
3. Update `run_tests.sh` to include the new test
4. Follow the existing naming convention: `test_*.py` 