@echo off
setlocal EnableExtensions

echo Resume Optimizer Setup
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 goto python_missing

REM Check if LaTeX (pdflatex) is installed
pdflatex --version >nul 2>&1
if errorlevel 1 goto latex_missing
goto continue_setup

:python_missing
echo Error: Python is not installed or not in PATH.
echo Please install Python 3.10+ from https://www.python.org/
pause
exit /b 1

:latex_missing
echo LaTeX compiler not found.
set /p install_tex=Do you want to install MiKTeX now? yes/no: 
if /i "%install_tex%"=="yes" goto install_miktex
echo Skipping MiKTeX installation. LaTeX features may not work.
goto continue_setup

:install_miktex
echo Downloading MiKTeX...
powershell -NoProfile -Command "Invoke-WebRequest 'https://miktex.org/download/win/miktexsetup-x64.zip' -OutFile 'miktex.zip'"
if not exist miktex.zip goto miktex_download_failed

echo Extracting MiKTeX...
powershell -NoProfile -Command "Expand-Archive -Path 'miktex.zip' -DestinationPath 'miktex' -Force"

echo Installing MiKTeX (this may take a while)...
if not exist miktex\miktexsetup_standalone.exe goto miktex_install_failed
miktex\miktexsetup_standalone.exe --quiet --package-set=basic install
if errorlevel 1 goto miktex_install_failed

echo MiKTeX installed successfully.
goto continue_setup

:miktex_download_failed
echo Error: Failed to download MiKTeX.
pause
exit /b 1

:miktex_install_failed
echo Error: MiKTeX installation failed.
pause
exit /b 1

:continue_setup
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 goto venv_failed

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 goto venv_failed

echo Installing dependencies...
pip install -r req.txt
if errorlevel 1 goto dependencies_failed

echo.
echo Creating .env file...
if exist .env goto env_exists
set /p api_key=Do you have your OpenAI API key ready? yes/no: 
if /i "%api_key%"=="yes" goto enter_api_key
(
    echo OPENAI_API_KEY=your_api_key_here
) > .env
echo .env file created with placeholder.
echo You can add your API key later by editing .env
echo Get an API key from: https://platform.openai.com/api-keys
goto after_env

:enter_api_key
set /p openai_key=Enter your OpenAI API key: 
(
    echo OPENAI_API_KEY=%openai_key%
) > .env
echo API key saved to .env
goto after_env

:env_exists
echo .env already exists. Skipping creation.

:after_env
echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. If you haven't added your API key, edit .env and add it
echo 2. Place or update your LaTeX resume as Resume.tex
echo 3. Run: python resume_builder.py --help
echo.
pause
exit /b 0

:venv_failed
echo Error: Failed to create or activate virtual environment.
pause
exit /b 1

:dependencies_failed
echo Error: Failed to install dependencies.
pause
exit /b 1