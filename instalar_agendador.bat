@echo off
chcp 65001 > nul
title Instalador da Tarefa Agendada no Windows
cls
echo ============================================================
echo      SafeBackup - Instalador de Tarefa no Windows
echo ============================================================
echo.
echo Este script registra o backup para executar todos os dias
echo automaticamente no Agendador de Tarefas do Windows.
echo.

set /p HORA="Digite o horario diario de execucao (ex: 02:00): "
if "%HORA%"=="" set HORA=02:00

set NOMETAREFA=SafeBackup_Task

if exist "%~dp0SafeBackup.exe" (
    set COMANDO="%~dp0SafeBackup.exe" --silent
) else if exist "%~dp0CFTV_SafeBackup.exe" (
    set COMANDO="%~dp0CFTV_SafeBackup.exe" --silent
) else if exist "%~dp0dist\SafeBackup\SafeBackup.exe" (
    set COMANDO="%~dp0dist\SafeBackup\SafeBackup.exe" --silent
) else if exist "%~dp0dist\CFTV_SafeBackup\CFTV_SafeBackup.exe" (
    set COMANDO="%~dp0dist\CFTV_SafeBackup\CFTV_SafeBackup.exe" --silent
) else (
    set COMANDO=python "%~dp0main.py" --silent
)

echo.
echo Registrando tarefa "%NOMETAREFA%" para as %HORA%...
schtasks /create /tn "%NOMETAREFA%" /tr "%COMANDO%" /sc DAILY /st %HORA% /f /rl HIGHEST

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo [SUCESSO] Tarefa registrada com exito no Windows!
    echo O backup sera executado todos os dias as %HORA%.
    echo ============================================================
) else (
    echo.
    echo [ERRO] Falha ao registrar tarefa. Execute este arquivo .bat
    echo como Administrador (Botao direito ^> Executar como administrador).
)

echo.
pause
