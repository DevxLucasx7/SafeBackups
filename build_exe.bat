@echo off
chcp 65001 > nul
title Compilador SafeBackup - Gerador de Executavel
cls
echo ============================================================
echo        SafeBackup - Gerador de Executavel (.exe)
echo ============================================================
echo.

echo [1/3] Verificando instalacao do PyInstaller...
python -m pip install --upgrade pip pyinstaller
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar o PyInstaller. Verifique a conexao com a internet.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Compilando executavel SafeBackup.exe...
python -m PyInstaller --noconfirm --onedir --windowed ^
    --name "SafeBackup" ^
    --add-data "core;core" ^
    --add-data "gui;gui" ^
    main.py

if %errorlevel% neq 0 (
    echo [ERRO] Falha durante a compilacao.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Copiando arquivos complementares para a pasta dist...
if exist "config.json" (
    copy /Y "config.json" "dist\SafeBackup\" > nul
)
if exist "instalar_agendador.bat" (
    copy /Y "instalar_agendador.bat" "dist\SafeBackup\" > nul
)
if exist "testar_backup.bat" (
    copy /Y "testar_backup.bat" "dist\SafeBackup\" > nul
)
if exist "criar_atalho_desktop.bat" (
    copy /Y "criar_atalho_desktop.bat" "dist\SafeBackup\" > nul
)
if not exist "dist\SafeBackup\logs" (
    mkdir "dist\SafeBackup\logs" > nul
)
if not exist "dist\SafeBackup\temp_backups" (
    mkdir "dist\SafeBackup\temp_backups" > nul
)

echo.
echo ============================================================
echo [SUCESSO] Executavel gerado na pasta:
echo           dist\SafeBackup\SafeBackup.exe
echo ============================================================
echo Voce pode mover toda a pasta "dist\SafeBackup" para qualquer
echo servidor ou computador Windows sem precisar de Python instalado!
echo.
pause
