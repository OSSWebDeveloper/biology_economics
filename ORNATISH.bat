@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Biologiya kursi - avtomatik o'rnatish

rem ============================================================
rem   SOZLAMALAR - kerak bo'lsa faqat shu qatorlarni o'zgartiring
rem ============================================================
set "GITHUB=https://github.com/OSSWebDeveloper/biology_economics"
set "TARMOQ=main"
set "JOY=C:\bio_moliya"
set "PORT=8000"
set "YORLIQ=Dasturga kirish"
set "YORLIQ2=Serverni to'xtatish"
set "PY_YUKLASH=https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
rem ============================================================

rem --- Administrator huquqi tekshiriladi ---
rem Ish stoli manzili ko'tarilishdan OLDIN aniqlanib, argument sifatida
rem uzatiladi. Sababi: UAC boshqa hisob bilan ko'tarilsa, ko'tarilgan
rem jarayon uchun "ish stoli" o'sha administratorning papkasi bo'lib
rem qoladi va yorliqlar foydalanuvchiga ko'rinmay qolardi.
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Administrator huquqi kerak. Ruxsat oynasi chiqadi...
    for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "BIO_ISHSTOLI=%%D"
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList '\"!BIO_ISHSTOLI!\"' -Verb RunAs" >nul 2>&1
    exit /b
)

set "BIO_ISHSTOLI=%~1"
if not defined BIO_ISHSTOLI (
    for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "BIO_ISHSTOLI=%%D"
)

cls
echo ============================================================
echo    BIOLOGIYA KURSI - MOLIYAVIY BOSHQARUV TIZIMI
echo    Avtomatik o'rnatish va yangilash
echo ============================================================
echo.
echo    Manba : %GITHUB%
echo    Joy   : %JOY%
echo    Port  : %PORT%
echo.
echo    Ma'lumotlar bazasi hech qachon o'chirilmaydi - faqat
echo    dastur fayllari yangilanadi.
echo.

set "SHUYER=%~dp0"
if "!SHUYER:~-1!"=="\" set "SHUYER=!SHUYER:~0,-1!"

rem ============================================================
call :sarlavha "1/8   Python tekshirilmoqda"
rem ============================================================
set "PY="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)

if not defined PY (
    echo    Mos Python topilmadi. Yuklab olinmoqda, bir necha daqiqa ketadi...
    powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PY_YUKLASH%' -OutFile '%TEMP%\python_setup.exe'" >nul 2>&1
    if errorlevel 1 goto :xato_internet
    echo    O'rnatilmoqda...
    "%TEMP%\python_setup.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1
    del /q "%TEMP%\python_setup.exe" >nul 2>&1
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY goto :xato_python

!PY! -c "import sys;print(sys.version.split()[0])" > "%TEMP%\bio_pyv.txt" 2>nul
set "PYV=?"
if exist "%TEMP%\bio_pyv.txt" set /p PYV=<"%TEMP%\bio_pyv.txt"
del /q "%TEMP%\bio_pyv.txt" >nul 2>&1
echo    Python !PYV! - tayyor.

rem ============================================================
call :sarlavha "2/8   Ishlab turgan server to'xtatilmoqda"
rem ============================================================
rem Server --noreload rejimida ishlaydi: yangi fayllar faqat u qayta ishga
rem tushgandan keyin kuchga kiradi. Shu sababli avval to'xtatiladi - shunda
rem fayllar ham, ma'lumotlar bazasi ham band bo'lmaydi.
set "PORT_JORIY=%PORT%"
if exist "%JOY%\port.txt" set /p PORT_JORIY=<"%JOY%\port.txt"

set "SERVER_ISHLAGAN="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /c:":!PORT_JORIY! " ^| findstr /i "LISTENING"') do (
    taskkill /PID %%P /T /F >nul 2>&1
    set "SERVER_ISHLAGAN=1"
)

if defined SERVER_ISHLAGAN (
    rem fayl qulflari bo'shashi uchun bir-ikki soniya kutamiz
    ping -n 3 127.0.0.1 >nul 2>&1
    echo    Server to'xtatildi - oxirida yangi versiya bilan qayta ochiladi.
) else (
    echo    Ishlab turgan server topilmadi.
)

rem ============================================================
call :sarlavha "3/8   Yangi nusxa yuklab olinmoqda"
rem ============================================================
set "ESKI_V=o'rnatilmagan"
if exist "%JOY%\versiya.txt" set /p ESKI_V=<"%JOY%\versiya.txt"

set "ZIP=%TEMP%\bio_moliya.zip"
set "VAQT=%TEMP%\bio_moliya_manba"
set "MANBA="
if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
if exist "%VAQT%" rd /s /q "%VAQT%" >nul 2>&1

rem GitHub fayllarni besh daqiqagacha keshda ushlab turadi. Shuning uchun
rem versiya alohida o'qilmaydi (kesh tufayli eski raqam kelib, yangilanish
rem o'tkazib yuborilar edi) - to'g'ridan-to'g'ri arxiv olinadi, manzilga
rem tasodifiy raqam qo'shilib keshdan emas, serverdan olish so'raladi.
set "CB=%RANDOM%%RANDOM%"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GITHUB%/archive/refs/heads/%TARMOQ%.zip?nocache=!CB!' -Headers @{'Cache-Control'='no-cache';'Pragma'='no-cache'} -OutFile '%ZIP%'" >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%VAQT%' -Force" >nul 2>&1
    for /d %%D in ("%VAQT%\*") do set "MANBA=%%D"
)

if defined MANBA (
    echo    Yuklab olindi.
) else (
    if exist "!SHUYER!\manage.py" (
        echo    Internetdan yuklab bo'lmadi - shu papkadagi nusxa ishlatiladi.
        set "MANBA=!SHUYER!"
    )
)
if not defined MANBA (
    if exist "%JOY%\manage.py" (
        echo    Internetdan yuklab bo'lmadi - o'rnatilgan nusxa saqlanib qoladi.
    ) else (
        goto :xato_internet
    )
)

set "YANGI_V=aniqlanmadi"
if defined MANBA (
    pushd "!MANBA!"
    if exist "versiya.txt" set /p YANGI_V=<versiya.txt
    popd
)

echo    Qurilmada : !ESKI_V!
echo    Yangi     : !YANGI_V!

rem ============================================================
call :sarlavha "4/8   Fayllar yangilanmoqda"
rem ============================================================
if not exist "%JOY%" mkdir "%JOY%"

rem Versiyalar teng bo'lsa ham nusxa ko'chiriladi: robocopy o'zgarmagan
rem fayllarni o'tkazib yuboradi, shu bilan "yangilandi deydi-yu, aslida
rem eski fayl qolib ketadi" degan holat butunlay yo'qoladi.
set "KOCHIR=1"
if not defined MANBA set "KOCHIR="
if defined MANBA if /i "!MANBA!"=="%JOY%" set "KOCHIR="

if not defined MANBA echo    Yangi fayllar yo'q - o'tkazib yuborildi.
if defined MANBA if /i "!MANBA!"=="%JOY%" echo    Dastur allaqachon shu papkada - ko'chirish shart emas.

if defined KOCHIR (
    if exist "%JOY%\db.sqlite3" (
        copy /y "%JOY%\db.sqlite3" "%JOY%\db_zaxira_oxirgi.sqlite3" >nul 2>&1
        echo    Bazadan zaxira olindi: db_zaxira_oxirgi.sqlite3
    )
    robocopy "!MANBA!" "%JOY%" /E /NFL /NDL /NJH /NJS /NP /XD ".venv" "__pycache__" ".git" "staticfiles" /XF "db.sqlite3" "db_zaxira_oxirgi.sqlite3" "maxfiy_kalit.txt" "port.txt" "server.log" >nul
    if errorlevel 8 goto :xato_nusxa
    echo    Dastur fayllari yangilandi, bazaga tegilmadi.
)

icacls "%JOY%" /grant "*S-1-5-32-545:(OI)(CI)M" /T /C /Q >nul 2>&1
echo    Yozish huquqi berildi.

rem ============================================================
call :sarlavha "5/8   Kutubxonalar tekshirilmoqda"
rem ============================================================
if not exist "%JOY%\manage.py" goto :xato_nusxa
set "VPY=%JOY%\.venv\Scripts\python.exe"
if not exist "!VPY!" (
    echo    Virtual muhit yaratilmoqda...
    !PY! -m venv "%JOY%\.venv"
)
if not exist "!VPY!" goto :xato_venv

"!VPY!" -m pip install --upgrade pip --disable-pip-version-check -q >nul 2>&1
"!VPY!" -m pip install -r "%JOY%\requirements.txt" --disable-pip-version-check -q
if errorlevel 1 (
    "!VPY!" -c "import django" >nul 2>&1
    if errorlevel 1 goto :xato_kutubxona
    echo    Internet yo'q, lekin kerakli kutubxonalar allaqachon o'rnatilgan.
)

"!VPY!" -c "import django;print(django.get_version())" > "%TEMP%\bio_djv.txt" 2>nul
set "DJV=?"
if exist "%TEMP%\bio_djv.txt" set /p DJV=<"%TEMP%\bio_djv.txt"
del /q "%TEMP%\bio_djv.txt" >nul 2>&1
echo    Django !DJV! - tayyor.

rem ============================================================
call :sarlavha "6/8   Ma'lumotlar bazasi tekshirilmoqda"
rem ============================================================
pushd "%JOY%"
> "%JOY%\port.txt" echo %PORT%
"!VPY!" manage.py migrate --noinput
if errorlevel 1 (
    popd
    goto :xato_baza
)
"!VPY!" manage.py boshlangich
"!VPY!" manage.py hisoblash
popd

rem ============================================================
call :sarlavha "7/8   Ish stoliga yorliqlar qo'yilmoqda"
rem ============================================================
rem Nomlar muhit o'zgaruvchisi orqali uzatiladi - buyruq satridagi
rem apostrof turli kompyuterlarda turlicha o'qilib ketmasligi uchun
set "BIO_JOY=%JOY%"
set "BIO_YORLIQ1=%YORLIQ%"
set "BIO_YORLIQ2=%YORLIQ2%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%JOY%\yorliqlar.ps1"
if errorlevel 1 (
    echo    Ogohlantirish: yorliqlarni yaratib bo'lmadi.
    echo    "%JOY%" papkasidagi .lnk fayllarini o'zingiz ish stoliga ko'chiring
    echo    yoki "%JOY%\Yorliqlarni_tiklash.bat" faylini ishga tushiring.
) else (
    echo    Ko'rinmasa - ish stolida bir marta F5 bosing.
)

rem ============================================================
call :sarlavha "8/8   Telefon bilan aloqa (Tailscale)"
rem ============================================================
call :tailscale

if exist "%ZIP%" del /q "%ZIP%" >nul 2>&1
if exist "%VAQT%" rd /s /q "%VAQT%" >nul 2>&1

set "HOZIRGI_V=?"
if exist "%JOY%\versiya.txt" set /p HOZIRGI_V=<"%JOY%\versiya.txt"

echo.
echo ============================================================
echo    TAYYOR - o'rnatilgan versiya: !HOZIRGI_V!
echo ============================================================
echo.
echo    Ish stolida ikkita yorliq paydo bo'ldi:
echo      "%YORLIQ%"  - sayt fon rejimida ishga tushadi va Chrome'da ochiladi
echo      "%YORLIQ2%"  - ishlab turgan serverni to'xtatadi
echo.
echo    Server ishlayotganda soat yonida (treyda) yashil barg belgisi turadi:
echo      chap tugma - saytni ochadi, o'ng tugma - yangilash va to'xtatish.
echo    Belgi ko'rinmasa, soat yonidagi "^" strelkasini bosib, uni
echo    sichqoncha bilan panelga tortib chiqaring.
echo.
echo    Manzil         : http://127.0.0.1:%PORT%/
echo    Dastur papkasi : %JOY%
echo    Xato izlash    : %JOY%\Tekshirish.bat
echo.
echo    SMS yuboradigan telefon qo'shish uchun:
echo      telefonni USB bilan ulang va "%JOY%\QURILMA_QOSHISH.bat"
echo      faylini ishga tushiring - qolganini u o'zi qiladi.
echo.
echo    Yangilanish chiqqanda shu faylni yana ishga tushiring -
echo    baza saqlanib qoladi, server esa o'zi qayta ishga tushadi.
echo.

rem Explorer orqali ochamiz. Sabab: ORNATISH.bat administrator huquqi bilan
rem ishlaydi, "start" esa shu huquqni dasturga ham beradi - keyin oddiy
rem "Serverni to'xtatish" yorlig'i uni to'xtata olmaydi. Explorer dasturni
rem foydalanuvchining odatdagi huquqi bilan ochadi.
rem
rem Bu yerda avval "Ishga tushirilsinmi? [Y/N]" savoli bor edi. U olib
rem tashlandi: "choice" buyrug'i bosilgan TUGMANI emas, chiqqan HARFNI
rem tekshiradi. Klaviatura tili rus yoki o'zbek kirillchasida tursa,
rem Y tugmasi "Н" harfini beradi - choice uni qabul qilmay faqat ovoz
rem chiqaradi va oyna qotib qolgandek ko'rinadi. Endi dastur shunchaki
rem ishga tushiriladi; kerak bo'lmasa "Serverni to'xtatish" bosiladi.
if defined SERVER_ISHLAGAN (
    echo    Server yangi versiya bilan qayta ishga tushirilmoqda...
) else (
    echo    Dastur ishga tushirilmoqda - Chrome o'zi ochiladi...
)
explorer.exe "%JOY%\Ishga_tushirish.vbs"

echo.
echo    Keyingi safar ochish uchun ish stolidagi "%YORLIQ%" yorlig'ini bosing.
echo    To'xtatish uchun - "%YORLIQ2%".
echo.
pause
goto :tamom


rem ============================================================
rem  Yordamchi bo'limlar
rem ============================================================

:sarlavha
echo.
echo  ------------------------------------------------------------
echo   %~1
echo  ------------------------------------------------------------
exit /b 0

rem ------------------------------------------------------------
rem  Tailscale: kompyuter bilan telefonni bitta SHAXSIY tarmoqqa
rem  ulaydi. SMS eslatmalarini telefon jo'natadi, telefon esa saytni
rem  shu tarmoq orqali ko'radi. Sayt internetga CHIQARILMAYDI -
rem  domen, oq IP, router sozlash kerak emas.
rem ------------------------------------------------------------
:tailscale
set "TS=%ProgramFiles%\Tailscale\tailscale.exe"
if exist "%TS%" goto :ts_bor

echo    SMS xabarlarni telefon jo'natadi. Buning uchun kompyuter bilan
echo    telefonni bitta shaxsiy tarmoqqa ulaydigan Tailscale dasturi kerak.
echo    U bepul va sayt internetga ochilmaydi - faqat sizning
echo    qurilmalaringiz ko'radi.
echo.
set "TSJ=h"
set /p TSJ="   Tailscale o'rnatilsinmi? [H/y]: "
if /i "%TSJ%"=="y" (
    echo    O'tkazib yuborildi. Keyinroq shu faylni qayta ishga tushirsangiz bo'ladi.
    exit /b 0
)

echo    Yuklab olinmoqda (37 MB)...
curl -L -s -o "%TEMP%\ts-setup.msi" "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi"
if not exist "%TEMP%\ts-setup.msi" (
    echo    Yuklab bo'lmadi - internetni tekshiring. Bu qadam o'tkazib yuborildi.
    exit /b 0
)
echo    O'rnatilmoqda...
msiexec /i "%TEMP%\ts-setup.msi" /qn /norestart
del /q "%TEMP%\ts-setup.msi" >nul 2>&1
if not exist "%TS%" (
    echo    Tailscale o'rnatilmadi. Bu qadam o'tkazib yuborildi.
    exit /b 0
)
echo    O'rnatildi.

:ts_bor
rem Hisobga kirilganmi?
"%TS%" status > "%TEMP%\ts_holat.txt" 2>&1
findstr /i /c:"Logged out" "%TEMP%\ts_holat.txt" >nul
if not errorlevel 1 (
    echo.
    echo    Endi hisobingizga kirish kerak - brauzer o'zi ochiladi.
    echo    Google yoki Microsoft hisobingiz bilan kiring.
    echo.
    echo    DIQQAT: telefonda ham AYNAN SHU hisobga kirasiz.
    echo.
    "%TS%" up --hostname=kurs-sayt
)
del /q "%TEMP%\ts_holat.txt" >nul 2>&1

rem Port faqat shaxsiy tarmoqdan ochiq bo'lsin (100.64.0.0/10 - Tailscale
rem diapazoni). Oddiy Wi-Fi yoki kafe tarmog'idan hech kim kira olmaydi.
netsh advfirewall firewall delete rule name="Bio Moliya - Tailscale (%PORT%)" >nul 2>&1
netsh advfirewall firewall add rule name="Bio Moliya - Tailscale (%PORT%)" dir=in action=allow protocol=TCP localport=%PORT% remoteip=100.64.0.0/10 >nul 2>&1
echo    Brandmauer: %PORT% porti faqat shaxsiy tarmoq uchun ochildi.

set "TS_IP="
for /f "usebackq delims=" %%i in (`"%TS%" ip -4 2^>nul`) do if not defined TS_IP set "TS_IP=%%i"
if defined TS_IP (
    echo    Telefon uchun manzil: http://%TS_IP%:%PORT%
    > "%JOY%\tailscale_manzil.txt" echo http://%TS_IP%:%PORT%
) else (
    echo    Hisobga hali kirilmagan - telefon uchun manzil keyin aniqlanadi.
)
exit /b 0

:xato
color 0C
echo.
echo  ============================================================
echo   XATO: %~1
if not "%~2"=="" echo         %~2
echo  ============================================================
echo.
pause
exit /b 1

:xato_internet
call :xato "Internetga ulanib bo'lmadi yoki manzil noto'g'ri." "%GITHUB%"
goto :tamom

:xato_python
call :xato "Python o'rnatilmadi." "python.org saytidan 3.12 yoki undan yangi versiyani qo'lda o'rnating."
goto :tamom

:xato_nusxa
call :xato "Dastur fayllari joyiga tushmadi." "%JOY% papkasini tekshiring."
goto :tamom

:xato_venv
call :xato "Virtual muhit yaratilmadi." "%JOY%\.venv papkasini o'chirib, qaytadan urinib ko'ring."
goto :tamom

:xato_kutubxona
call :xato "Kutubxonalarni o'rnatib bo'lmadi." "Internet aloqasini tekshiring."
goto :tamom

:xato_baza
call :xato "Ma'lumotlar bazasini tekshirib bo'lmadi." "Tekshirish.bat orqali batafsil xatoni ko'ring."
goto :tamom

:tamom
endlocal
exit /b 0
