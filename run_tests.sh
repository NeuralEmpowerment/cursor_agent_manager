#!/bin/bash

# Run Tests Script
# Convenience script to run all tests in the tests/ directory

echo "🧪 Running Agent Monitor Tests"
echo "============================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected. Activating..."
    source venv/bin/activate
fi

# Run telemetry tests
echo ""
echo "📊 Running Telemetry System Tests..."
python tests/test_telemetry.py

if [ $? -ne 0 ]; then
    echo "❌ Telemetry tests failed"
    exit 1
fi

# Run quickstart tests
echo ""
echo "🚀 Running Quickstart Tests..."
python tests/test_quickstart.py

if [ $? -ne 0 ]; then
    echo "❌ Quickstart tests failed"
    exit 1
fi

# Run priority logic tests
echo ""
echo "🎯 Running Priority Logic Tests..."
python tests/test_priority_logic.py

if [ $? -ne 0 ]; then
    echo "❌ Priority logic tests failed"
    exit 1
fi

echo ""
echo "✅ All tests passed successfully!"
echo ""
echo "You can also run individual tests:"
echo "  python tests/test_telemetry.py"
echo "  python tests/test_quickstart.py"
echo "  python tests/test_priority_logic.py" 