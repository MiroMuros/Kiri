#!/bin/bash

# Run tests for the Clothing Pattern Generator application

# Create necessary directories
mkdir -p /tmp/clothing_pattern_app/uploads
mkdir -p /tmp/clothing_pattern_app/output

# Run unit tests
echo "Running unit tests..."
python3 -m unittest tests/unit_tests.py

# Run integration tests
echo "Running integration tests..."
python3 -m unittest tests/integration_tests.py

echo "Tests completed."
