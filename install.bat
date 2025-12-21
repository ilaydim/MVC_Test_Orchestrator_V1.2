@echo off
REM MVC Test Orchestrator Installation Script (Windows)

echo.
echo ========================================
echo   MVC Test Orchestrator v1.2
echo   Installation Script (Windows)
echo ========================================
echo.

REM Check Python version
echo [1/5] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

python --version
echo [OK] Python found

REM Check Python version is 3.9+
python -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.9 or higher is required.
    pause
    exit /b 1
)

REM Create virtual environment (optional)
echo.
set /p CREATE_VENV="Do you want to create a virtual environment? (recommended) [Y/n]: "
if /i "%CREATE_VENV%"=="n" goto skip_venv
if /i "%CREATE_VENV%"=="no" goto skip_venv

echo.
echo [2/5] Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment created at .venv
echo.
echo [INFO] To activate it, run: .venv\Scripts\activate
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat
echo [OK] Virtual environment activated
goto install_deps

:skip_venv
echo [SKIP] Skipping virtual environment creation

:install_deps
echo.
echo [3/5] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed successfully

REM Create .env file if it doesn't exist
echo.
if not exist .env (
    echo [4/5] Creating .env file...
    if exist env.example (
        copy env.example .env >nul
        echo [OK] .env file created from env.example
    ) else (
        echo GOOGLE_API_KEY=your_api_key_here > .env
        echo [OK] .env file created
    )
    echo [WARNING] Please edit .env and add your Google Gemini API key!
    echo [INFO] Get your API key from: https://makersuite.google.com/app/apikey
) else (
    echo [4/5] .env file already exists
)

REM Create data directory
echo.
echo [5/5] Creating data directory...
if not exist data mkdir data
echo [OK] Data directory created

echo.
echo ========================================
echo   Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env file and add your GOOGLE_API_KEY
echo   2. Run: python -m src.cli.mvc_arch_cli --help
echo.
echo Example usage:
echo   python -m src.cli.mvc_arch_cli create-srs --user-idea "Your project idea" --output data/srs_document.txt
echo.

pause

