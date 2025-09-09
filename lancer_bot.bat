@echo off
title BOT DISCORD - Ton Cousin
echo ========================================
echo    Lancement du bot Discord "Le Cousin"
echo ========================================
echo.

echo [1/3] Deplacement dans le dossier du bot...
cd /d "C:\Users\Mokui\Documents\BotDiscord"
echo OK
echo.

echo [2/3] Activation de l'environnement virtuel...
call .\venv\Scripts\activate
if errorlevel 1 (
    echo ❌ Erreur : impossible d'activer le venv !
    pause
    exit /b
)
echo OK
echo.

echo [3/3] Demarrage du bot (main.py)...
python .\main.py
if errorlevel 1 (
    echo ❌ Erreur pendant l'execution de main.py !
) else (
    echo ✅ Bot execute avec succes !
)

echo.
echo ========================================
echo   Execution terminee
echo ========================================
pause
