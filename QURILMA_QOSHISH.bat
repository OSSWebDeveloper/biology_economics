@echo off
rem ====================================================================
rem  YANGI QURILMA QO'SHISH
rem  SMS yuboradigan telefonni to'liq sozlaydi.
rem
rem  Telefonni USB kabel bilan ulang va shu faylni ikki marta bosing.
rem  Telefonda "USB debugging" yoqilgan bo'lishi kerak:
rem    Sozlamalar -> Telefon haqida -> "Build number" ni 7 marta bosing
rem    -> Dasturchi sozlamalari -> USB debugging = yoq
rem ====================================================================
title Yangi qurilma qo'shish - Kurs SMS
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0qurilma_qoshish.ps1" %*

if errorlevel 1 (
    echo.
    echo    Xatolik bilan tugadi.
    pause
)
