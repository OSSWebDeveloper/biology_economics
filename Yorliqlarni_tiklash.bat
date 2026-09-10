@echo off
rem ============================================================
rem   Biologiya kursi - ish stoli yorliqlarini tiklash
rem
rem   Agar o'rnatishdan keyin ish stolida yorliqlar ko'rinmasa,
rem   shu faylni ishga tushiring. Dastur qayta o'rnatilmaydi,
rem   ma'lumotlar bazasiga ham tegilmaydi - faqat yorliqlar
rem   qaytadan yaratiladi.
rem ============================================================
setlocal EnableExtensions
title Biologiya kursi - yorliqlarni tiklash

rem --- Administrator huquqi: umumiy ish stoliga yozish uchun kerak ---
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo   Administrator huquqi so'raladi...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs" >nul 2>&1
    exit /b
)

set "JOY=%~dp0"
if "%JOY:~-1%"=="\" set "JOY=%JOY:~0,-1%"

set "BIO_JOY=%JOY%"
set "BIO_YORLIQ1=Dasturga kirish"
set "BIO_YORLIQ2=Serverni to'xtatish"

echo.
echo   Yorliqlar tiklanmoqda...
echo   Dastur papkasi: %BIO_JOY%
echo.

if not exist "%JOY%\yorliqlar.ps1" (
    echo   XATO: yorliqlar.ps1 topilmadi.
    echo   ORNATISH.bat orqali dasturni yangilang.
    echo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%JOY%\yorliqlar.ps1"
set "NATIJA=%ERRORLEVEL%"

echo.
if "%NATIJA%"=="0" (
    echo   Tayyor. Ish stolini bir marta yangilang ^(F5^).
) else (
    echo   Ba'zi yorliqlar yaratilmadi.
    echo   "%BIO_JOY%" papkasidagi .lnk fayllarini o'zingiz
    echo   ish stoliga ko'chirib qo'ying.
)
echo.
pause
endlocal
