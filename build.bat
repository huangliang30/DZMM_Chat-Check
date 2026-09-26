@echo off
chcp 65001 > nul
echo ============================================
echo   AI Chat Viewer - Build Script
echo   聊天记录查看器 - 编译脚本
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

echo [2/2] Building executable with PyInstaller...
pyinstaller --onefile --windowed ^
    --name "AI_Chat_Viewer" ^
    --add-data "%APPDATA%\..\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\tkinterdnd2;tkinterdnd2" ^
    --hidden-import tkinter ^
    --hidden-import tkinterdnd2 ^
    --hidden-import tkinterdnd2.tkdnd ^
    --hidden-import tkinterdnd2.tkdnd_wrapper ^
    --hidden-import tkinter.ttk ^
    --collect-all tkinterdnd2 ^
    --icon=NONE ^
    "chat_viewer.py"

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\AI_Chat_Viewer.exe
echo ============================================
pause
