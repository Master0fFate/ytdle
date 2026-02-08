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

:: Check for icon file
set "ICON_ARG="
if exist "icon.ico" (
    echo [INFO] Found icon.ico, will be used for the executable.
    set "ICON_ARG=--icon=icon.ico"
) else (
    echo [INFO] icon.ico not found, building without custom icon.
)

:: Build Option Selection
echo.
echo Select Build Type:
echo 1. Standard (external binaries NOT bundled - smaller size)
echo 2. Standalone (FFmpeg bundled - larger size, self-contained)
echo 3. Full Standalone (FFmpeg + aria2c bundled - largest size, fully self-contained)
echo.
set /p build_choice="Enter your choice (1, 2, or 3): "

set "FFMPEG_ARG="
set "ARIA2C_ARG="

if "%build_choice%"=="3" (
    :: Full standalone - bundle both ffmpeg and aria2c
    set "MISSING_DEPS="

    if not exist "ffmpeg.exe" (
        set "MISSING_DEPS=ffmpeg.exe"
    )
    if not exist "aria2c.exe" (
        if "!MISSING_DEPS!"=="" (
            set "MISSING_DEPS=aria2c.exe"
        ) else (
            set "MISSING_DEPS=!MISSING_DEPS!, aria2c.exe"
        )
    )

    if not "!MISSING_DEPS!"=="" (
        echo.
        echo [ERROR] Missing required binaries: !MISSING_DEPS!
        echo Cannot bundle. Aborting build.
        pause
        exit /b 1
    )

    echo.
    echo [INFO] Bundling ffmpeg.exe and aria2c.exe into the executable.
    set "FFMPEG_ARG=--add-binary "ffmpeg.exe;.""
    set "ARIA2C_ARG=--add-binary "aria2c.exe;.""

) else if "%build_choice%"=="2" (
    :: Standalone - bundle ffmpeg only
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

    if exist "aria2c.exe" (
        echo [INFO] Found aria2c.exe - it will be available if users want to use it.
        set "ARIA2C_ARG=--add-binary "aria2c.exe;.""
    )
) else (
    echo.
    echo [INFO] Building without bundling external binaries.
    echo [INFO] Users will need ffmpeg.exe and/or aria2c.exe separately for full functionality.
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
:: --hidden-import: Ensure core modules are included.
:: --log-level WARN: Reduce noise in the output.

pyinstaller --console --onefile --name "YTDLE" --clean --collect-all yt_dlp ^
    --hidden-import core.async_manager ^
    --hidden-import core.database ^
    --hidden-import core.downloader ^
    --hidden-import core.config ^
    --hidden-import core.history ^
    --hidden-import core.errors ^
    --hidden-import core.network ^
    --hidden-import core.utils ^
    --hidden-import core.dependencies ^
    --hidden-import core.logger ^
    --hidden-import ui.main_window ^
    --hidden-import ui.styles ^
    --hidden-import ui.components.title_bar ^
    --hidden-import ui.components.history_dialog ^
    %FFMPEG_ARG% %ARIA2C_ARG% %ICON_ARG% --log-level WARN main.py

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
