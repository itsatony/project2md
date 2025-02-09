#!/bin/bash
set -e

# Ensure we're using the latest build tools
python -m pip install --upgrade pip build twine

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
