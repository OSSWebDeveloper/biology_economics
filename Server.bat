@echo off
rem Serverni fon rejimida ishga tushiradi. Ishga_tushirish.vbs shuni chaqiradi.
rem Bevosita ishga tushirilsa ham ishlaydi - oyna ochiq qoladi.
cd /d "%~dp0"

set "PORT=8000"
if exist port.txt set /p PORT=<port.txt

rem Tailscale o'rnatilgan bo'lsa server barcha interfeyslarda tinglaydi -
rem shunda telefondagi "Kurs SMS" ilovasi shaxsiy tarmoq orqali saytga kira
rem oladi. Tailscale yo'q bo'lsa faqat shu kompyuterning o'zida ochiladi.
rem Port tashqi tarmoqdan yopiq: brandmauerda faqat 100.64.0.0/10 ga ruxsat.
set "MANZIL=127.0.0.1"
if exist "%ProgramFiles%\Tailscale\tailscale.exe" set "MANZIL=0.0.0.0"

if not exist ".venv\Scripts\python.exe" (
    echo XATO: .venv topilmadi. ORNATISH.bat ni qayta ishga tushiring.>> "server.log"
    exit /b 1
)

echo.>> "server.log"
echo ===== %DATE% %TIME% - server ishga tushmoqda, %MANZIL%:%PORT% =====>> "server.log"
".venv\Scripts\python.exe" manage.py runserver %MANZIL%:%PORT% --noreload >> "server.log" 2>&1
