@echo off
rem ===========================================================================
rem  ALS progress app - start it on this computer (Windows).
rem
rem  Double-click this file, or a desktop shortcut to it. The app opens in the
rem  browser at http://localhost:8501 and answers only on this computer.
rem  Keep the black window open while you use the app; close it to stop the app.
rem
rem  First start: makes a private Python environment in the .venv folder and
rem  installs the packages in requirements.txt. This needs internet once, or a
rem  "wheels" folder with the packages - see README, "Install without internet".
rem  Later starts reuse .venv and need no internet.
rem ===========================================================================
setlocal
cd /d "%~dp0"
title ALS progress app
set "URL=http://localhost:8501"
set "VPY=.venv\Scripts\python.exe"

rem ---- Already running? Then only open it in the browser. -------------------
curl --silent --noproxy "*" --max-time 2 --output nul "%URL%/_stcore/health" >nul 2>&1
if errorlevel 1 goto :find_python
echo The app is already running. Opening %URL% ...
start "" "%URL%"
exit /b 0

rem ---- Python 3.10 or newer --------------------------------------------------
:find_python
set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :venv
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto :venv
echo.
echo  Python 3.10 or newer was not found on this computer.
echo  Install it from https://www.python.org/downloads/windows/
echo    - "Install for current user" does not need administrator rights.
echo    - Tick "Add python.exe to PATH".
echo  Then double-click start.bat again.
goto :fail

rem ---- Private Python environment in .venv (made on the first start) --------
:venv
if not exist "%VPY%" goto :make_venv
"%VPY%" -c "import sys" >nul 2>&1
if not errorlevel 1 goto :packages
rem A .venv copied from another computer does not work here: make a new one.
echo The .venv folder does not work on this computer. Making a new one ...
rmdir /s /q .venv
:make_venv
echo First start: making a private Python environment in .venv ...
%PY% -m venv .venv
if errorlevel 1 goto :fail

rem ---- Packages: install on the first start and when requirements.txt changes
:packages
fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if not errorlevel 1 goto :run
echo Installing the app's Python packages. This takes a few minutes, only this time ...
if exist wheels\ goto :install_offline
"%VPY%" -m pip install --disable-pip-version-check -r requirements.txt
goto :installed
:install_offline
echo Using the packages in the wheels folder, no internet needed.
"%VPY%" -m pip install --disable-pip-version-check --no-index --find-links wheels -r requirements.txt
:installed
if errorlevel 1 goto :pip_failed
copy /y requirements.txt .venv\requirements.installed >nul

rem ---- Start the app ---------------------------------------------------------
rem .streamlit\config.toml: only this computer (localhost), port 8501, no usage statistics.
:run
echo.
echo  ALS progress app: %URL%  - only on this computer
echo  Data: "%CD%\data\raw_data.xlsx" - edit it here or in Excel
echo  Keep this window open while you use the app. Close it to stop the app.
echo.
"%VPY%" -m streamlit run app.py
echo.
echo  The app has stopped.
pause
exit /b 0

:pip_failed
echo.
echo  Could not install the packages. This computer may have no internet, or it
echo  needs a proxy. See README, "Install without internet".
:fail
echo.
pause
exit /b 1
