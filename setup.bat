@echo off
echo Resume Optimizer Setup
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r req.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Creating .env file...
if exist .env (
    echo .env already exists. Skipping creation.
) else (
    set /p api_key="Do you have your OpenAI API key ready? (yes/no): "
    if /i "%api_key%"=="yes" (
        set /p openai_key="Enter your OpenAI API key: "
        (
            echo OPENAI_API_KEY=%openai_key%
        ) > .env
        echo.
        echo API key saved to .env
    ) else (
        (
            echo OPENAI_API_KEY=your_api_key_here
        ) > .env
        echo .env file created with placeholder.
        echo.
        echo You can add your API key later by editing .env
        echo Get an API key from: https://platform.openai.com/api-keys
    )
    echo.
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. If you haven't added your API key, edit .env and add it
echo 2. Place or update your LaTeX resume as Resume.tex
echo 3. Run: python resume_builder.py --help
echo.
pause
