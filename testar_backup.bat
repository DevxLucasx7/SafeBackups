@echo off
chcp 65001 > nul
title Teste de Backup CFTV
cls
echo ============================================================
echo         Iniciando Teste Manual de Backup (Modo CLI)
echo ============================================================
echo.

if exist "%~dp0SafeBackup.exe" (
    echo Executando via executavel local...
    "%~dp0SafeBackup.exe" --silent
) else if exist "%~dp0CFTV_SafeBackup.exe" (
    echo Executando via executavel local...
    "%~dp0CFTV_SafeBackup.exe" --silent
) else if exist "%~dp0dist\SafeBackup\SafeBackup.exe" (
    echo Executando via executavel compilado em dist...
    "%~dp0dist\SafeBackup\SafeBackup.exe" --silent
) else if exist "%~dp0dist\CFTV_SafeBackup\CFTV_SafeBackup.exe" (
    echo Executando via executavel compilado em dist...
    "%~dp0dist\CFTV_SafeBackup\CFTV_SafeBackup.exe" --silent
) else (
    echo Executando via interpretador Python...
    python "%~dp0main.py" --silent
)

echo.
echo ============================================================
echo Execucao finalizada. Verifique os logs na pasta "logs".
echo ============================================================
pause
