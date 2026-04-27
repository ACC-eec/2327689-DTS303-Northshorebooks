@echo off
REM Northshore Books - Windows Setup Script
echo ========================================
echo Northshore Books - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)
echo.

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

echo [3/6] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

echo [4/6] Setting up environment file...
if exist .env (
    echo .env file already exists. Skipping...
) else (
    if exist ENV_EXAMPLE.txt (
        copy ENV_EXAMPLE.txt .env >nul
        echo .env file created from ENV_EXAMPLE.txt
        echo IMPORTANT: Please edit .env and update SECRET_KEY and database credentials
    ) else (
        echo WARNING: ENV_EXAMPLE.txt not found. Please create .env manually.
    )
)
echo.

echo [5/6] Creating storage/logs directory...
if not exist storage\logs (
    mkdir storage\logs
    echo storage\logs directory created.
) else (
    echo storage\logs directory already exists.
)
echo.

echo [6/6] Running database migrations...
python manage.py makemigrations
if errorlevel 1 (
    echo WARNING: makemigrations failed. This is normal if database is not configured yet.
) else (
    python manage.py migrate
    if errorlevel 1 (
        echo WARNING: migrate failed. Please check your database configuration in .env
    ) else (
        echo Migrations completed successfully.
    )
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and update:
echo    - SECRET_KEY (generate a new one for production)
echo    - Database credentials (DB_NAME, DB_USER, DB_PASSWORD, etc.)
echo.
echo 2. Create MySQL database:
echo    CREATE DATABASE northshore_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
echo.
echo 3. Run migrations again (if database is now configured):
echo    python manage.py migrate
echo.
echo 4. Create superuser:
echo    python manage.py createsuperuser
echo.
echo 5. Run development server:
echo    python manage.py runserver
echo.
echo ========================================
pause
