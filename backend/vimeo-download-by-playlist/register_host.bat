@echo off
setlocal

:: Путь к файлу манифеста
set MANIFEST_PATH=%~dp0com.vimeo.downloader.json

:: Путь в реестре для Chrome
set CHROME_REGISTRY_KEY=HKCU\Software\Google\Chrome\NativeMessagingHosts\com.vimeo.downloader

:: Путь в реестре для Edge
set EDGE_REGISTRY_KEY=HKCU\Software\Microsoft\Edge\NativeMessagingHosts\com.vimeo.downloader

:: Регистрация для Chrome
reg add "%CHROME_REGISTRY_KEY%" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f

:: Регистрация для Edge
reg add "%EDGE_REGISTRY_KEY%" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f

echo Native messaging host registered successfully.
pause
