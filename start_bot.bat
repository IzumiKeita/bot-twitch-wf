@echo off
setlocal EnableDelayedExpansion
title Bot de Warframe Standalone
color 0A

:: Intentar forzar UTF-8 para caracteres especiales
chcp 65001 > nul

echo =======================================================
echo          WARFRAME BOT STANDALONE - LAUNCHER
echo =======================================================
echo.

:: 1. BUSCAR PYTHON
:: Intentamos 'python', 'py', y 'python3' en orden.
set "PYTHON_CMD="

:: Prueba 1: 'python'
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
    goto FOUND_PYTHON
)

:: Prueba 2: 'py' (Python Launcher para Windows)
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=py"
    goto FOUND_PYTHON
)

:: Prueba 3: 'python3'
python3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python3"
    goto FOUND_PYTHON
)

:: Si llegamos aqui, no encontramos Python
echo [ERROR] No se ha encontrado ninguna instalacion de Python.
echo Por favor, instala Python 3.10 o superior desde https://www.python.org/downloads/
echo IMPORTANTE: Marca la casilla "Add Python to PATH" durante la instalacion.
echo.
pause
exit /b 1

:FOUND_PYTHON
echo [INFO] Python encontrado: !PYTHON_CMD!
!PYTHON_CMD! --version

:: 2. CONFIGURAR ENTORNO VIRTUAL (.venv)
:: Usamos .venv estandar en lugar de 'venv' para seguir buenas practicas, pero soportamos ambos si ya existe 'venv'
set "VENV_DIR=.venv"
if exist "venv" set "VENV_DIR=venv"

if not exist "!VENV_DIR!" (
    echo [INFO] Creando entorno virtual en carpeta '!VENV_DIR!'...
    !PYTHON_CMD! -m venv !VENV_DIR!
    if !errorlevel! neq 0 (
        echo [ERROR] Fallo al crear el entorno virtual.
        pause
        exit /b 1
    )
)

:: 3. INSTALAR DEPENDENCIAS
:: Verificamos si existe la carpeta Scripts (Windows)
if exist "!VENV_DIR!\Scripts\python.exe" (
    set "VENV_PYTHON=!VENV_DIR!\Scripts\python.exe"
    set "VENV_PIP=!VENV_DIR!\Scripts\pip.exe"
) else (
    echo [ERROR] No se encuentra el ejecutable de Python en el entorno virtual.
    echo Intenta borrar la carpeta '!VENV_DIR!' y ejecutar de nuevo.
    pause
    exit /b 1
)

:: Actualizar pip si es necesario (opcional, pero recomendado)
:: "!VENV_PYTHON!" -m pip install --upgrade pip >nul 2>&1

echo [INFO] Verificando dependencias...
"!VENV_PIP!" install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Fallo al instalar las dependencias.
    pause
    exit /b 1
)

:: 4. MENU PRINCIPAL
:MENU
cls
echo =======================================================
echo          WARFRAME BOT STANDALONE - MENU
echo =======================================================
echo.
echo 1. Iniciar Bot (Recomendado)
echo 2. Generador de Token (Avanzado - Requiere App ID)
echo 3. Actualizar Dependencias
echo 4. Salir
echo.

set /p option="Elige una opcion [1-4]: "

if "%option%"=="1" goto START_BOT
if "%option%"=="2" goto AUTH_TOOL
if "%option%"=="3" goto UPDATE_DEPS
if "%option%"=="4" goto EXIT

echo Opcion no valida.
pause
goto MENU

:START_BOT
cls
echo =======================================================
echo          WARFRAME BOT STANDALONE - EJECUTANDO
echo =======================================================
echo [INFO] Iniciando bot con: !VENV_PYTHON!
echo.
"!VENV_PYTHON!" bot.py

if !errorlevel! neq 0 (
    echo.
    echo [ALERTA] El bot se ha cerrado con un error o ha sido detenido.
)

echo.
echo Presiona cualquier tecla para volver al menu...
pause > nul
goto MENU

:AUTH_TOOL
cls
echo =======================================================
echo          HERRAMIENTA DE AUTENTICACION
echo =======================================================
echo.
echo [ADVERTENCIA] Esta herramienta requiere que hayas creado una aplicacion
echo en la consola de desarrolladores de Twitch (dev.twitch.tv).
echo.
echo Necesitas configurar TWITCH_CLIENT_ID y TWITCH_CLIENT_SECRET en .env
echo.
echo Si solo quieres un token rapido, usa: https://twitchapps.com/tmi/
echo.
pause
"!VENV_PYTHON!" auth_twitch.py
echo.
pause
goto MENU

:UPDATE_DEPS
cls
echo [INFO] Forzando actualizacion de dependencias...
"!VENV_PIP!" install -r requirements.txt --upgrade
echo.
echo [OK] Completado.
pause
goto MENU

:EXIT
exit
