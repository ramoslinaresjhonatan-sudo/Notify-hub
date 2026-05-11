@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Iniciando Reporte de Tiempo de Carga...
if not exist "..\..\..\venv" (
    echo [ERROR] No se encontro el entorno virtual (venv^).
    echo Por favor, ejecuta 'setup.bat' en la raiz.
    pause
    exit /b 1
)

call "..\..\..\venv\Scripts\activate"
python "..\ReporteDeTiempoDeCarga.py"
pause
