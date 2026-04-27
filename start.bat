@echo off
setlocal
REM Northshore Books - one-click launcher for the marker.
REM Does everything end-to-end: venv, deps, .env, storage dirs, migrations,
REM admin user, sample books, then opens the site in your browser.

echo ========================================
echo Northshore Books - Starting
echo ========================================
echo.

REM 0) Python check
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Install Python 3.11+ from python.org and try again.
    pause
    exit /b 1
)

REM 1) Virtual environment
if not exist venv (
    echo [1/7] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/7] Virtual environment already exists.
)

REM 2) Activate
echo [2/7] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM 3) Dependencies (pip skips anything already installed)
echo [3/7] Installing dependencies (first run takes a minute)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

REM 4) .env (defaults to SQLite for local marker run)
if not exist .env (
    echo [4/7] Creating .env from ENV_EXAMPLE.txt (SQLite default)...
    copy ENV_EXAMPLE.txt .env >nul
) else (
    echo [4/7] .env already present.
)

REM 5) Runtime directories
if not exist storage\logs mkdir storage\logs
echo [5/7] Runtime directories ready.

REM 6) Migrations
echo [6/7] Running database migrations...
python manage.py migrate --noinput
if errorlevel 1 (
    echo ERROR: Migrations failed. See message above.
    pause
    exit /b 1
)

REM 7) Admin user + sample books
echo [7/7] Creating admin user and seeding sample books...
python manage.py shell --command "from django.contrib.auth import get_user_model; U=get_user_model(); U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin','admin@example.com','NorthshoreAdmin1234!')"
python manage.py seed_from_openlibrary 2>nul
if errorlevel 1 (
    echo    (seeder skipped - non-fatal, the site still runs)
)

echo.
echo ========================================
echo  Northshore Books is ready.
echo  Opening http://127.0.0.1:8000 in your browser...
echo.
echo  Admin URL:   /admin/
echo  Username:    admin
echo  Password:    NorthshoreAdmin1234!
echo  API docs:    /api/docs/
echo.
echo  Press Ctrl+C to stop the server.
echo ========================================
echo.

REM Launch browser then start server
start "" http://127.0.0.1:8000/
python manage.py runserver
