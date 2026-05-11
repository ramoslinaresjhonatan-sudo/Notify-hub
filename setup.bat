@echo off
setlocal enabledelayedexpansion

:: Colores simples para la consola
set "GREEN=[OK]"
set "RED=[ERROR]"
set "BLUE=[INFO]"

echo %BLUE% Iniciando instalacion de dependencias para Notify-hub...

:: 1. Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED% Python no esta instalado o no se encuentra en el PATH.
    echo Por favor, instala Python y vuelve a intentarlo.
    pause
    exit /b 1
)

:: 2. Crear entorno virtual si no existe
if not exist venv (
    echo %BLUE% Creando entorno virtual (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %RED% No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo %GREEN% Entorno virtual creado.
) else (
    echo %BLUE% El entorno virtual ya existe.
)

:: 3. Activar entorno virtual e instalar dependencias
echo %BLUE% Activando entorno virtual e instalando requerimientos...
call venv\Scripts\activate

:: Actualizar pip
python -m pip install --upgrade pip

:: Instalar requerimientos
if exist requirements.txt (
    echo %BLUE% Instalando paquetes desde requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo %RED% Hubo un error al instalar las dependencias.
        pause
        exit /b 1
    )
    echo %GREEN% Dependencias instaladas correctamente.
) else (
    echo %RED% No se encontro el archivo requirements.txt.
)

:: 4. Instalar navegadores de Playwright (necesario por el requirements.txt)
echo %BLUE% Instalando navegadores para Playwright...
playwright install
if %errorlevel% neq 0 (
    echo %RED% No se pudieron instalar los navegadores de Playwright.
) else (
    echo %GREEN% Navegadores de Playwright listos.
)

echo.
echo %GREEN% ¡Configuracion completada con exito!
echo Para activar el entorno manualmente usa: call venv\Scripts\activate
echo.
pause
