@echo off
setlocal enabledelayedexpansion

set "ENV_DIR=.venv"
set "APP_NAME=YouTubeDownloader"
set "ICON_FILE=icon.ico"

echo ========================================
echo YouTube Downloader Build Script
echo ========================================
echo.

:: Перевіряємо наявність Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python first.
    pause
    exit /b 1
)

:: Створюємо віртуальне середовище якщо немає
if not exist %ENV_DIR% (
    echo [1/5] Creating virtual environment...
    python -m venv %ENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.

    echo [2/5] Activating virtual environment...
    call %ENV_DIR%\Scripts\activate

    echo [3/5] Installing packages from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install packages!
        pause
        exit /b 1
    )
    echo [OK] Packages installed.
) else (
    echo [1/5] Virtual environment already exists.
    echo [2/5] Activating virtual environment...
    call %ENV_DIR%\Scripts\activate
)

:: Перевіряємо наявність PyInstaller
echo [3/5] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Перевіряємо наявність іконки
echo [4/5] Checking icon file...
if exist "%ICON_FILE%" (
    echo [OK] Icon file found: %ICON_FILE%
    set "ICON_ARG=--icon=%ICON_FILE%"
) else (
    echo [WARNING] Icon file not found! Building without icon.
    echo [INFO] To add icon, place icon.ico in the current directory.
    set "ICON_ARG="
)

:: Отримуємо шлях до customtkinter
echo Getting customtkinter path...
for /f "tokens=1,* delims=: " %%A in ('pip show customtkinter ^| findstr "Location:"') do (
    set "CUSTOMTKINTER_PATH=%%B"
)
set "CUSTOMTKINTER_PATH=!CUSTOMTKINTER_PATH: =!"

:: Формуємо шлях для add-data (правильний формат для Windows)
set "ADD_DATA=!CUSTOMTKINTER_PATH!\customtkinter;customtkinter/"

echo.
echo ========================================
echo Building executable...
echo ========================================
echo.

:: Збираємо команду PyInstaller
set "BUILD_CMD=pyinstaller --noconfirm --windowed %ICON_ARG% --onefile --name %APP_NAME%"

:: Додаємо customtkinter як data file
if exist "!CUSTOMTKINTER_PATH!\customtkinter" (
    set "BUILD_CMD=!BUILD_CMD! --add-data "!ADD_DATA!""
    echo Adding customtkinter from: !CUSTOMTKINTER_PATH!
) else (
    echo [WARNING] customtkinter path not found!
)

:: Додаємо додаткові приховані імпорти
set "BUILD_CMD=!BUILD_CMD! --hidden-import yt_dlp"
set "BUILD_CMD=!BUILD_CMD! --hidden-import yt_dlp.extractor"
set "BUILD_CMD=!BUILD_CMD! --hidden-import yt_dlp.downloader"
set "BUILD_CMD=!BUILD_CMD! --hidden-import customtkinter"
set "BUILD_CMD=!BUILD_CMD! --hidden-import tkinter"

:: Додаємо іконку як data file (щоб вона була доступна в exe)
if exist "%ICON_FILE%" (
    set "BUILD_CMD=!BUILD_CMD! --add-data "%ICON_FILE%;.""
)

:: Додаємо файл для збірки
set "BUILD_CMD=!BUILD_CMD! app.py"

:: Виводимо команду для відладки
echo.
echo Command: !BUILD_CMD!
echo.

:: Виконуємо збірку
!BUILD_CMD!

:: Перевіряємо результат
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [5/5] Build completed successfully!
echo.

:: Організовуємо вихідні файли
echo Organizing build files...
if exist builded (
    echo Deleting existing builded folder...
    rmdir /s /q builded
)

if exist dist (
    echo Renaming dist to builded...
    rename dist builded
) else (
    echo [WARNING] dist folder not found!
)

if exist build (
    echo Deleting build folder...
    rmdir /s /q build
)

if exist %APP_NAME%.spec (
    echo Deleting %APP_NAME%.spec...
    del %APP_NAME%.spec
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
if exist builded\%APP_NAME%.exe (
    echo Executable: builded\%APP_NAME%.exe
    echo Size:
    dir builded\%APP_NAME%.exe | find "%APP_NAME%.exe"
) else (
    echo [ERROR] Executable not found in builded folder!
)

echo.
echo Done!
pause
endlocal