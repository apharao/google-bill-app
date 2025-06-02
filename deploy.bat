@echo off
SETLOCAL

REM === CONFIG ===
SET "ZIP_FILE=C:\Users\alexi\Downloads\restaurant_bill_splitter.zip"
SET "TEMP_DIR=%~dp0temp_extract"

REM === CLEANUP PREVIOUS TEMP ===
IF EXIST "%TEMP_DIR%" (
    echo 🔄 Removing previous temp folder...
    rmdir /S /Q "%TEMP_DIR%"
)

REM === EXTRACT ZIP ===
echo 📦 Extracting ZIP to temp folder...
powershell -Command "Expand-Archive -LiteralPath '%ZIP_FILE%' -DestinationPath '%TEMP_DIR%'"

REM === COPY CONTENTS TO REPO ===
echo 📁 Copying contents to working directory...
xcopy /E /Y "%TEMP_DIR%\*" .

REM === SHOW CHANGES ===
echo 🔍 Git status:
git status

echo 🔍 Git diff (line changes):
git diff --stat

REM === GIT COMMIT & PUSH ===
git add .
git commit -m "Deploy latest update from ZIP"
git push origin main

echo ✅ App updated and pushed to GitHub!
pause
ENDLOCAL
