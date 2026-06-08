#!/bin/bash
echo "=== Wanderlust Travel Agency - Setup ==="

# Install dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To run the app:"
echo "  python run.py"
echo ""
echo "Then open: http://localhost:5000"
echo ""
echo "Admin login:"
echo "  Email:    admin@travelagency.com"
echo "  Password: admin123"
