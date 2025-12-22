@echo off
setlocal EnableDelayedExpansion

:: Change to the directory where the script is located
cd /d "%~dp0"
echo Current working directory: %CD%

:: Check if PyInstaller is installed
where pyinstaller >nul 2>&1
if %errorLevel% neq 0 (
    echo PyInstaller is not found in PATH.
    echo Installing PyInstaller...
    pip install pyinstaller
    if %errorLevel% neq 0 (
        echo Failed to install PyInstaller. Please install it manually.
        pause
        exit /b 1
    )
)

echo.
echo ========================================================
echo Starting YTDLE Build Process
echo ========================================================
echo.

:: Build Option Selection
echo Select Build Type:
echo 1. Standard (FFmpeg NOT bundled - smaller size, requires ffmpeg.exe nearby)
echo 2. Standalone (FFmpeg bundled - larger size, self-contained)
echo.
set /p build_choice="Enter your choice (1 or 2): "

set "FFMPEG_ARG="
if "%build_choice%"=="2" (
    if exist "ffmpeg.exe" (
        echo.
        echo [INFO] Bundling ffmpeg.exe into the executable.
        set "FFMPEG_ARG=--add-binary "ffmpeg.exe;.""
    ) else (
        echo.
        echo [ERROR] ffmpeg.exe not found in the current directory!
        echo Cannot bundle FFmpeg. Aborting build.
        pause
        exit /b 1
    )
) else (
    echo.
    echo [INFO] Building without bundling FFmpeg.
)

:: Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

echo.
echo Building executable...
:: PyInstaller Command Explanation:
:: --console: Show console (required for CLI args), hidden by code if GUI mode.
:: --onefile: Bundle everything into a single .exe file.
:: --name "YTDLE": Name the output executable.
:: --clean: Clean PyInstaller cache and remove temporary files before building.
:: --collect-all yt_dlp: Ensure all yt-dlp plugins/extractors are included.
:: --log-level WARN: Reduce noise in the output.

pyinstaller --console --onefile --name "YTDLE" --clean --collect-all yt_dlp %FFMPEG_ARG% --log-level WARN main.py

if %errorLevel% equ 0 (
    echo.
    echo ========================================================
    echo Build Successful!
    echo The executable can be found in the "dist" folder.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Build Failed!
    echo Please check the error messages above.
    echo ========================================================
)

pause
