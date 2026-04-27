#!/bin/bash

# Northshore Books - Unix/Linux/Mac Setup Script

set -e  # Exit on error

echo "========================================"
echo "Northshore Books - Setup Script"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

echo "[1/6] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully."
fi
echo ""

echo "[2/6] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "Virtual environment activated."
echo ""

echo "[3/6] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully."
echo ""

echo "[4/6] Setting up environment file..."
if [ -f ".env" ]; then
    echo ".env file already exists. Skipping..."
else
    if [ -f "ENV_EXAMPLE.txt" ]; then
        cp ENV_EXAMPLE.txt .env
        echo ".env file created from ENV_EXAMPLE.txt"
        echo "IMPORTANT: Please edit .env and update SECRET_KEY and database credentials"
    else
        echo "WARNING: ENV_EXAMPLE.txt not found. Please create .env manually."
    fi
echo ""

echo "[5/6] Creating storage/logs directory..."
if [ ! -d "storage/logs" ]; then
    mkdir -p storage/logs
    echo "storage/logs directory created."
else
    echo "storage/logs directory already exists."
fi
echo ""

echo "[6/6] Running database migrations..."
python manage.py makemigrations || echo "WARNING: makemigrations failed. This is normal if database is not configured yet."
python manage.py migrate || echo "WARNING: migrate failed. Please check your database configuration in .env"
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and update:"
echo "   - SECRET_KEY (generate a new one for production)"
echo "   - Database credentials (DB_NAME, DB_USER, DB_PASSWORD, etc.)"
echo ""
echo "2. Create MySQL database:"
echo "   CREATE DATABASE northshore_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo ""
echo "3. Run migrations again (if database is now configured):"
echo "   python manage.py migrate"
echo ""
echo "4. Create superuser:"
echo "   python manage.py createsuperuser"
echo ""
echo "5. Run development server:"
echo "   python manage.py runserver"
echo ""
echo "========================================"
