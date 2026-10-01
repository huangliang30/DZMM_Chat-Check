@echo off
chcp 65001 > nul
echo ============================================
echo   AI Chat Check - Build Script
echo   聊天记录查看器 - 编译脚本
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist\AI_Chat_Check.exe" del /q "dist\AI_Chat_Check.exe"

echo [2/2] Building executable with PyInstaller (AI_Chat_Viewer.spec)...
python -m PyInstaller AI_Chat_Viewer.spec --noconfirm
if errorlevel 1 (
    echo.
    echo   Build FAILED! 请检查上方错误信息。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\AI_Chat_Check.exe
echo ============================================
pause
