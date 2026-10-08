@echo off
rem Coblings launcher for Windows (needs Python 3.11+, nothing else).
rem Messages stay ASCII-only so they render under any console codepage.
setlocal

set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%src"

py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto use_py

python -c "import sys" >nul 2>&1
if not errorlevel 1 goto use_python

echo [coblings] Python 3 not found. Install Python 3.11+ and try again.
exit /b 1

:use_py
set "PY=py -3"
goto run

:use_python
set "PY=python"

:run
rem Incremental build: skips work when nothing under src\ changed.
%PY% "%ROOT%tools\build.py"
if errorlevel 1 exit /b 1

rem No chcp here: the CLI encodes output in the console's own codepage
rem (e.g. cp950), so CJK text renders without switching to 65001.
%PY% -m coblings %*
exit /b %ERRORLEVEL%
