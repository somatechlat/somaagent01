#!/bin/bash
set -e

echo "Installing missing Python dependencies..."
pip install --no-cache-dir fasta2a==0.5.0
pip install --no-cache-dir fastmcp==2.3.4
pip install --no-cache-dir mcp==1.13.1

echo "Verifying installations..."
python -c "import fasta2a; print('fasta2a installed successfully')"
python -c "import fastmcp; print('fastmcp installed successfully')"
python -c "import mcp; print('mcp installed successfully')"

echo "All dependencies installed successfully!"