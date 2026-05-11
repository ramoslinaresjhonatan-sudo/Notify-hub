@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Iniciando Automatizacion de NotifyHub...
if not exist "..\..\..\venv" (
    echo [ERROR] No se encontro el entorno virtual (venv^).
    echo Por favor, ejecuta 'setup.bat' en la raiz.
    pause
    exit /b 1
)

call "..\..\..\venv\Scripts\activate"
python "..\NotifyHub-Automatizacion.py"
pause
