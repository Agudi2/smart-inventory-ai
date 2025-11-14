#!/bin/bash

# Script to seed the database with sample data
# Usage: ./run_seed.sh

echo "=========================================="
echo "Database Seeding Script"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Run seed script
echo ""
python seed_data.py

echo ""
echo "=========================================="
echo "Seeding complete!"
echo "=========================================="
