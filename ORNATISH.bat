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
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Administrator huquqi kerak. Ruxsat oynasi chiqadi...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" >nul 2>&1
    exit /b
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
call :sarlavha "1/7   Python tekshirilmoqda"
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
call :sarlavha "2/7   Versiya solishtirilmoqda"
rem ============================================================
set "ESKI_V=o'rnatilmagan"
if exist "%JOY%\versiya.txt" set /p ESKI_V=<"%JOY%\versiya.txt"

set "YANGI_V="
set "RAW=!GITHUB:https://github.com/=https://raw.githubusercontent.com/!"
del /q "%TEMP%\bio_versiya.txt" >nul 2>&1
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '!RAW!/%TARMOQ%/versiya.txt' -OutFile '%TEMP%\bio_versiya.txt'" >nul 2>&1
if exist "%TEMP%\bio_versiya.txt" set /p YANGI_V=<"%TEMP%\bio_versiya.txt"
del /q "%TEMP%\bio_versiya.txt" >nul 2>&1

echo    Qurilmada : !ESKI_V!
if defined YANGI_V (
    echo    GitHub'da : !YANGI_V!
) else (
    echo    GitHub'da : aniqlanmadi
)

set "YANGILASH=1"
if defined YANGI_V if /i "!ESKI_V!"=="!YANGI_V!" if exist "%JOY%\manage.py" set "YANGILASH="

if defined YANGILASH (
    echo    Natija    : dastur yangilanadi.
) else (
    echo    Natija    : oxirgi versiya turibdi, fayllar o'zgarmaydi.
)

rem ============================================================
call :sarlavha "3/7   Dastur yuklab olinmoqda"
rem ============================================================
set "ZIP=%TEMP%\bio_moliya.zip"
set "VAQT=%TEMP%\bio_moliya_manba"
set "MANBA="

if not defined YANGILASH (
    echo    O'tkazib yuborildi.
    goto :kutubxonalar
)

if exist "%VAQT%" rd /s /q "%VAQT%" >nul 2>&1
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GITHUB%/archive/refs/heads/%TARMOQ%.zip' -OutFile '%ZIP%'" >nul 2>&1
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
if not defined MANBA goto :xato_internet

rem ============================================================
call :sarlavha "4/7   Fayllar yangilanmoqda"
rem ============================================================
if not exist "%JOY%" mkdir "%JOY%"

if /i "!MANBA!"=="%JOY%" (
    echo    Dastur allaqachon shu papkada - ko'chirish shart emas.
) else (
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

:kutubxonalar
rem ============================================================
call :sarlavha "5/7   Kutubxonalar tekshirilmoqda"
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
call :sarlavha "6/7   Ma'lumotlar bazasi tekshirilmoqda"
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
call :sarlavha "7/7   Ish stoliga yorliqlar qo'yilmoqda"
rem ============================================================
rem PowerShell uchun nomlardagi apostrof ikkilantiriladi
set "YORLIQ_PS=%YORLIQ:'=''%"
set "YORLIQ2_PS=%YORLIQ2:'=''%"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $d = [Environment]::GetFolderPath('CommonDesktopDirectory'); if (-not $d -or -not (Test-Path $d)) { $d = [Environment]::GetFolderPath('Desktop') }; foreach ($eski in @('Biologiya kursi.lnk','Dasturni yopish.lnk')) { $y = Join-Path $d $eski; if (Test-Path $y) { Remove-Item -LiteralPath $y -Force; Write-Host ('    Eski yorliq olib tashlandi: ' + $eski) } }; $royxat = @( @('%YORLIQ_PS%','Ishga_tushirish.vbs','bio.ico','Biologiya kursi - dasturni ochish'), @('%YORLIQ2_PS%','Toxtatish.vbs','bio_stop.ico','Biologiya kursi - serverni toxtatish') ); foreach ($r in $royxat) { $dest = Join-Path $d ($r[0] + '.lnk'); $src = Join-Path '%JOY%' ($r[0] + '.lnk'); if (Test-Path $src) { Copy-Item -LiteralPath $src -Destination $dest -Force }; $l = $ws.CreateShortcut($dest); $l.TargetPath = Join-Path '%JOY%' $r[1]; $l.WorkingDirectory = '%JOY%'; $l.IconLocation = Join-Path '%JOY%' $r[2]; $l.Description = $r[3]; $l.Save(); Write-Host ('    ' + $dest) }"
if errorlevel 1 echo    Ogohlantirish: yorliqlar yaratilmadi, %JOY% papkasidagi .lnk fayllarini o'zingiz ish stoliga ko'chiring.

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
echo    Manzil         : http://127.0.0.1:%PORT%/
echo    Dastur papkasi : %JOY%
echo    Xato izlash    : %JOY%\Tekshirish.bat
echo.
echo    Yangilanish chiqqanda shu faylni yana ishga tushiring -
echo    versiya solishtiriladi, baza esa saqlanib qoladi.
echo.

choice /c YN /n /m "   Hozir ishga tushirilsinmi?   [Y = ha, N = yo'q] "
if errorlevel 2 goto :tamom
rem Explorer orqali ochamiz. Sabab: ORNATISH.bat administrator huquqi bilan
rem ishlaydi, "start" esa shu huquqni dasturga ham beradi - keyin oddiy
rem "Serverni to'xtatish" yorlig'i uni to'xtata olmaydi. Explorer dasturni
rem foydalanuvchining odatdagi huquqi bilan ochadi.
explorer.exe "%JOY%\Ishga_tushirish.vbs"
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
