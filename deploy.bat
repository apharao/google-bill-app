@echo off
REM Set the path to your extracted ZIP folder
SET ZIP_PATH=C:\Users\alexi\Downloads\restaurant_bill_splitter
REM Copy contents to current folder (your repo)
xcopy /E /Y "%ZIP_PATH%\\*" .

REM Add, commit, and push via Git
git add .
git commit -m "Deploy latest update from ZIP"
git push origin main

echo ✅ App updated and pushed to GitHub!
pause
