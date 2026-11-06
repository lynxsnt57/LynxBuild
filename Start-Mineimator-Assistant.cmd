@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import tkinter" >nul 2>&1
if errorlevel 1 goto missing
py -3 "%~dp0assistant\app.py"
if errorlevel 1 goto failed
exit /b 0
:missing
echo Python 3 or tkinter is not available.
echo Please send a screenshot of this message.
pause
exit /b 1
:failed
echo The assistant could not start.
echo Please send a screenshot of the error above.
pause
exit /b 1
