@echo off
chcp 65001 > nul
title Criar Atalho na Area de Trabalho
cls
echo ============================================================
echo      SafeBackup - Criador de Atalho na Area de Trabalho
echo ============================================================
echo.

set TARGET="%~dp0SafeBackup.exe"
if not exist %TARGET% (
    set TARGET="%~dp0CFTV_SafeBackup.exe"
)
if not exist %TARGET% (
    set TARGET="%~dp0dist\SafeBackup\SafeBackup.exe"
)
if not exist %TARGET% (
    set TARGET="%~dp0dist\CFTV_SafeBackup\CFTV_SafeBackup.exe"
)

if not exist %TARGET% (
    echo [ERRO] O executavel SafeBackup.exe nao foi encontrado nesta pasta.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'SafeBackup.lnk')); $s.TargetPath = '%TARGET:"=%'; $s.WorkingDirectory = [System.IO.Path]::GetDirectoryName('%TARGET:"=%'); $s.IconLocation = '%TARGET:"=%'; $s.Description = 'Backup Automatizado Seguro'; $s.Save()"

if %errorlevel% equ 0 (
    echo [SUCESSO] Atalho 'SafeBackup' criado na sua Area de Trabalho!
) else (
    echo [AVISO] Nao foi possivel criar o atalho automaticamente.
)

echo.
pause
