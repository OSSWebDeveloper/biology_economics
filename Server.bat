@echo off
rem Serverni fon rejimida ishga tushiradi. Ishga_tushirish.vbs shuni chaqiradi.
rem Bevosita ishga tushirilsa ham ishlaydi - oyna ochiq qoladi.
cd /d "%~dp0"

set "PORT=8000"
if exist port.txt set /p PORT=<port.txt

if not exist ".venv\Scripts\python.exe" (
    echo XATO: .venv topilmadi. ORNATISH.bat ni qayta ishga tushiring.>> "server.log"
    exit /b 1
)

echo.>> "server.log"
echo ===== %DATE% %TIME% - server ishga tushmoqda, port %PORT% =====>> "server.log"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:%PORT% --noreload >> "server.log" 2>&1
