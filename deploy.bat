@echo off
setlocal

REM Define paths
set ZIP_NAME=restaurant_bill_splitter.zip
set DOWNLOADS=%USERPROFILE%\Downloads
set ZIP_PATH=%DOWNLOADS%\%ZIP_NAME%
set TEMP_UNZIP=%DOWNLOADS%\restaurant_bill_splitter_temp

REM Check if zip exists
if not exist "%ZIP_PATH%" (
    echo ❌ ZIP file not found: %ZIP_PATH%
    pause
    exit /b
)

REM Clean previous temp extract
if exist "%TEMP_UNZIP%" (
    rmdir /s /q "%TEMP_UNZIP%"
)

REM Extract ZIP to temp folder (requires PowerShell)
echo 📦 Extracting ZIP to %TEMP_UNZIP% ...
powershell -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%TEMP_UNZIP%'"

REM Copy contents from extracted ZIP to current folder (your Git repo)
echo 📁 Copying files into repo ...
xcopy "%TEMP_UNZIP%\*" . /E /Y /I

REM Stage, commit, and push
git add .
git commit -m "Deploy latest update from ZIP"
git push origin main

echo ✅ App deployed and pushed to GitHub!
pause
