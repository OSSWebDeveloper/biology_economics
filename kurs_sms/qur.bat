@echo off
rem Kurs SMS - APK qurish. Android Studio kerak emas.
rem Ishlatish:  qur.bat assembleRelease    yoki    qur.bat assembleDebug
setlocal
cd /d "%~dp0"
set "JAVA_HOME=D:\android\jdk"
set "ANDROID_HOME=D:\android\sdk"
set "ANDROID_SDK_ROOT=D:\android\sdk"
set "GRADLE_USER_HOME=D:\android\gradle-home"
set "PATH=%JAVA_HOME%\bin;%PATH%"
if "%~1"=="" (
    call "D:\android\gradle-8.9\bin\gradle.bat" assembleRelease
) else (
    call "D:\android\gradle-8.9\bin\gradle.bat" %*
)
endlocal
