# =====================================================================
#  YANGI QURILMA QO'SHISH
# ---------------------------------------------------------------------
#  SMS yuboradigan telefonni noldan to'liq sozlaydi:
#    - adb (Android asbobi) - yo'q bo'lsa o'zi yuklab oladi
#    - telefonga Tailscale + Kurs SMS ilovasi
#    - barcha ruxsatlar, batareya va fon cheklovlari
#    - saytga ulanish (12 xonalik kodni o'zi yaratib, o'zi uzatadi)
#
#  Telefonda oldindan "USB debugging" yoqilgan bo'lishi kerak:
#    Sozlamalar -> Telefon haqida -> "Build number" ni 7 marta bosing
#    -> Sozlamalar -> Dasturchi sozlamalari -> USB debugging = yoq
#
#  Ishga tushirish: QURILMA_QOSHISH.bat
# =====================================================================

param(
    [switch]$Savolsiz,     # hech narsa so'ramaydi
    [switch]$FaqatIlova    # Tailscale qadamlarini o'tkazib yuboradi
)

$ErrorActionPreference = "Continue"

$SAYT      = $PSScriptRoot                      # bu skript sayt papkasida turadi
$PAKET     = "uz.olimjonov.kurssms"
$TS_PAKET  = "com.tailscale.ipn"
$ASBOB     = Join-Path $SAYT "asboblar"
$TS_EXE    = "$env:ProgramFiles\Tailscale\tailscale.exe"
$VPY       = Join-Path $SAYT ".venv\Scripts\python.exe"

$TS_APK_URL = "https://pkgs.tailscale.com/stable/tailscale-android-universal-1.102.4.apk"
$ADB_URL    = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"

# Telefonga beriladigan ruxsatlar
$RUXSATLAR = @(
    @{ nom = "android.permission.SEND_SMS";           izoh = "SMS jo'natish" },
    @{ nom = "android.permission.READ_PHONE_STATE";   izoh = "SIM kartalar ro'yxati" },
    @{ nom = "android.permission.POST_NOTIFICATIONS"; izoh = "Bildirishnomalar (Android 13+)" }
)

# ------------------------------------------------------------ yordamchi

function Sarlavha($matn) {
    Write-Host ""
    Write-Host ("  " + $matn) -ForegroundColor Cyan
    Write-Host ("  " + ("-" * $matn.Length)) -ForegroundColor DarkCyan
}

function Yaxshi($matn) { Write-Host "  [+] $matn" -ForegroundColor Green }
function Oddiy($matn)  { Write-Host "      $matn" -ForegroundColor Gray }
function Ogoh($matn)   { Write-Host "  [!] $matn" -ForegroundColor Yellow }
function Yomon($matn)  { Write-Host "  [X] $matn" -ForegroundColor Red }

function Toxta($matn, $izoh = "") {
    Write-Host ""
    Yomon $matn
    if ($izoh) { Oddiy $izoh }
    Write-Host ""
    if (-not $Savolsiz) {
        Write-Host "  Yopish uchun Enter ni bosing..." -ForegroundColor DarkGray
        Read-Host | Out-Null
    }
    exit 1
}

function HaMi($savol) {
    if ($Savolsiz) { return $true }
    Write-Host ""
    $javob = Read-Host "  $savol (ha / yo'q)"
    return ($javob -match '^\s*[hHyY]')
}

function Son($matn) {
    $son = 0
    if ([int]::TryParse(("" + $matn).Trim(), [ref]$son)) { return $son }
    return -1
}

function Shell($buyruq) {
    return (& $ADB -s $QURILMA shell $buyruq | Out-String).Trim()
}

function Xususiyat($nom) { return (Shell "getprop $nom") }

# Telefonda paket bormi
function PaketBor($paket) {
    return ((Shell "pm list packages $paket") -match [regex]::Escape($paket))
}

# Saytdagi Django buyrug'ini ishga tushiradi va chiqishini qaytaradi
function Django($kod) {
    Push-Location $SAYT
    try {
        return (& $VPY manage.py shell -c $kod | Out-String)
    } finally {
        Pop-Location
    }
}

# =====================================================================

Clear-Host
Write-Host ""
Write-Host "  ===================================================" -ForegroundColor White
Write-Host "    YANGI QURILMA QO'SHISH" -ForegroundColor White
Write-Host "    SMS yuboradigan telefonni sozlash" -ForegroundColor White
Write-Host "  ===================================================" -ForegroundColor White

# ------------------------------------------------------- 1) sayt joyida mi
Sarlavha "1. Sayt tekshirilmoqda"

if (-not (Test-Path (Join-Path $SAYT "manage.py"))) {
    Toxta "Bu skript sayt papkasida turishi kerak." "Hozirgi joy: $SAYT"
}
if (-not (Test-Path $VPY)) {
    # Ishlab chiqish kompyuterida .venv bo'lmasligi mumkin - umumiy Python
    $umumiy = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($umumiy) {
        $VPY = $umumiy.Source
        Oddiy "(.venv yo'q - umumiy Python ishlatiladi)"
    } else {
        Toxta "Sayt to'liq o'rnatilmagan (.venv topilmadi)." "Avval ORNATISH.bat ni ishga tushiring."
    }
}
Yaxshi "Sayt: $SAYT"

$PORT = "8000"
$portFayl = Join-Path $SAYT "port.txt"
if (Test-Path $portFayl) { $PORT = (Get-Content $portFayl -Raw).Trim() }
Oddiy "Port: $PORT"

# ---------------------------------------------------------- 2) ilova APK si
Sarlavha "2. Ilova fayli"

$APK = Join-Path $SAYT "ilova\kurs_sms.apk"
# Ishlab chiqish kompyuterida yangiroq nusxa bo'lsa - o'shanisi
$DEV_APK = "D:\kurs_sms\app\build\outputs\apk\release\app-release.apk"
if ((Test-Path $DEV_APK) -and (Test-Path $APK)) {
    if ((Get-Item $DEV_APK).LastWriteTime -gt (Get-Item $APK).LastWriteTime) {
        Copy-Item $DEV_APK $APK -Force
        Oddiy "Yangi qurilgan nusxa olindi (ishlab chiqish kompyuteri)."
    }
} elseif ((Test-Path $DEV_APK) -and -not (Test-Path $APK)) {
    New-Item -ItemType Directory -Force (Split-Path $APK) | Out-Null
    Copy-Item $DEV_APK $APK -Force
}

if (-not (Test-Path $APK)) {
    Toxta "Ilova fayli topilmadi: $APK" ("APK ochiq repozitoriyga qo'yilmaydi. " +
        "Uni ishlab chiqish kompyuterida qur.bat assembleRelease bilan quring " +
        "yoki tayyor nusxasini shu papkaga qo'ying.")
}

$ilovaVersiya = "?"
$ilovaVersiyaFayl = Join-Path $SAYT "ilova\versiya.txt"
if (Test-Path $ilovaVersiyaFayl) { $ilovaVersiya = (Get-Content $ilovaVersiyaFayl -Raw).Trim() }
Yaxshi ("Kurs SMS v$ilovaVersiya (" + [math]::Round((Get-Item $APK).Length / 1MB, 1) + " MB)")

# ------------------------------------------------------------------ 3) adb
Sarlavha "3. Android asbobi (adb)"

$ADB = $null
foreach ($joy in @(
    (Join-Path $ASBOB "platform-tools\adb.exe"),
    "D:\android\sdk\platform-tools\adb.exe",
    "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
)) {
    if ($joy -and (Test-Path $joy)) { $ADB = $joy; break }
}
if (-not $ADB) {
    $buyruq = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($buyruq) { $ADB = $buyruq.Source }
}

if (-not $ADB) {
    Oddiy "adb topilmadi - Google saytidan yuklab olinadi (15 MB)..."
    New-Item -ItemType Directory -Force $ASBOB | Out-Null
    $zip = Join-Path $env:TEMP "platform-tools.zip"
    & "$env:SystemRoot\System32\curl.exe" -L --retry 3 -sS -o $zip $ADB_URL
    if (-not (Test-Path $zip)) { Toxta "adb yuklab olinmadi - internetni tekshiring." }
    tar -xf $zip -C $ASBOB
    Remove-Item $zip -ErrorAction SilentlyContinue
    $ADB = Join-Path $ASBOB "platform-tools\adb.exe"
    if (-not (Test-Path $ADB)) { Toxta "adb ochilmadi." }
}
Yaxshi "adb: $ADB"

# ------------------------------------------------------------- 4) telefon
Sarlavha "4. Telefon qidirilmoqda"

& $ADB start-server | Out-Null

$QURILMA = $null
$ruxsatOgoh = $false
$topilmadiOgoh = $false

for ($urinish = 0; $urinish -lt 90; $urinish++) {
    $qatorlar = (& $ADB devices) | Where-Object { $_ -match "^\S+\s+(device|unauthorized|offline)\s*$" }
    $ruxsatsiz = $qatorlar | Where-Object { $_ -match "unauthorized\s*$" }
    $tayyor    = $qatorlar | Where-Object { $_ -match "\sdevice\s*$" }

    if ($tayyor) {
        if (@($tayyor).Count -gt 1) {
            Ogoh "Bir nechta qurilma ulangan, birinchisi olinadi."
        }
        $QURILMA = (@($tayyor)[0] -split "\s+")[0]
        break
    }

    if ($ruxsatsiz -and -not $ruxsatOgoh) {
        Ogoh "Telefon ulandi, lekin ruxsat berilmagan."
        Oddiy "Telefon ekranida 'USB orqali nosozliklarni tuzatishga ruxsat"
        Oddiy "berilsinmi?' oynasi chiqadi - 'Ruxsat berish' ni bosing."
        Oddiy "('Bu kompyuterga doim ruxsat' ni belgilab qo'ying)"
        $ruxsatOgoh = $true
    }
    elseif (-not $qatorlar -and -not $topilmadiOgoh) {
        Ogoh "Telefon topilmadi. Tekshiring:"
        Oddiy "1. USB kabel ulanganmi (zaryadlash emas, ma'lumot kabeli bo'lsin)"
        Oddiy "2. Telefonda: Sozlamalar -> Telefon haqida ->"
        Oddiy "   'Build number' ni 7 marta bosing"
        Oddiy "3. Keyin: Sozlamalar -> Dasturchi sozlamalari -> USB debugging = YOQ"
        Write-Host ""
        Oddiy "Kutilmoqda... (to'xtatish uchun Ctrl+C)"
        $topilmadiOgoh = $true
    }
    Start-Sleep -Seconds 2
}

if (-not $QURILMA) { Toxta "Telefon topilmadi (3 daqiqa kutildi)." }

$nomi = ((Xususiyat "ro.product.manufacturer") + " " + (Xususiyat "ro.product.model")).Trim()
$sdk  = Xususiyat "ro.build.version.sdk"
Yaxshi "Telefon: $nomi (Android $(Xususiyat 'ro.build.version.release'), SDK $sdk)"

# --------------------------------------------------- 5) shaxsiy tarmoq
$manzil = ""

if (-not $FaqatIlova) {
    Sarlavha "5. Shaxsiy tarmoq (Tailscale)"

    if (-not (Test-Path $TS_EXE)) {
        Ogoh "Kompyuterda Tailscale o'rnatilmagan."
        Oddiy "ORNATISH.bat ni ishga tushirib, Tailscale qadamini bajaring."
        Oddiy "Hozircha ilova o'rnatiladi, ulanishni keyin qilasiz."
        $FaqatIlova = $true
    }
}

if (-not $FaqatIlova) {
    # Kompyuter hisobga kirganmi
    $tsHolat = (& $TS_EXE status | Out-String)
    if ($tsHolat -match "Logged out") {
        Ogoh "Kompyuter Tailscale hisobiga kirmagan."
        Oddiy "ORNATISH.bat ni qayta ishga tushiring va hisobga kiring."
        $FaqatIlova = $true
    }
}

if (-not $FaqatIlova) {
    # Telefonda Tailscale bormi
    if (PaketBor $TS_PAKET) {
        Yaxshi "Telefonda Tailscale bor"
    } else {
        Oddiy "Telefonga Tailscale o'rnatiladi (100 MB, biroz vaqt oladi)..."
        $tsApk = Join-Path $env:TEMP "tailscale-android.apk"
        if (-not (Test-Path $tsApk)) {
            & "$env:SystemRoot\System32\curl.exe" -L --retry 3 -sS -o $tsApk $TS_APK_URL
        }
        if (Test-Path $tsApk) {
            $n = (& $ADB -s $QURILMA install -r $tsApk | Out-String)
            if ($n -match "Success") { Yaxshi "Telefonga Tailscale o'rnatildi" }
            else { Ogoh "Tailscale o'rnatilmadi - Play Market dan qo'lda o'rnating" }
        } else {
            Ogoh "Tailscale yuklab olinmadi - Play Market dan qo'lda o'rnating"
        }
    }

    # Telefon tarmoqqa kirganmi - kompyuterdagi ro'yxatdan bilinadi
    $telefonNomi = ((Xususiyat "ro.product.model") -replace '[^A-Za-z0-9]', '-').ToLower()
    $tarmoqda = ((& $TS_EXE status | Out-String) -match "android")

    if (-not $tarmoqda) {
        Write-Host ""
        Ogoh "ENDI TELEFONDA BITTA ISH BOR:"
        Oddiy "1. Ochilgan Tailscale ilovasida 'Get started' / 'Log in' ni bosing"
        Oddiy "2. Kompyuterdagi AYNAN SHU hisob bilan kiring"
        Oddiy "3. VPN ruxsati so'ralsa - 'OK' bosing"
        Write-Host ""
        Shell "monkey -p $TS_PAKET -c android.intent.category.LAUNCHER 1" | Out-Null

        Oddiy "Kutilmoqda (3 daqiqa)..."
        for ($i = 0; $i -lt 90; $i++) {
            Start-Sleep -Seconds 2
            if (((& $TS_EXE status | Out-String) -match "android")) { $tarmoqda = $true; break }
        }
    }

    if ($tarmoqda) {
        Yaxshi "Telefon shaxsiy tarmoqqa qo'shildi"
        $ip = (& $TS_EXE ip -4 | Select-Object -First 1).Trim()
        if ($ip) { $manzil = "http://${ip}:$PORT" }
    } else {
        Ogoh "Telefon tarmoqqa qo'shilmadi - ulanishni keyin qilasiz"
    }
}

# --------------------------------------------------------- 6) ilova
Sarlavha "6. Kurs SMS ilovasi"

if (PaketBor $PAKET) {
    Oddiy "Telefonda allaqachon bor - ustidan yangilanadi"
    Oddiy "(sozlamalar va saytga ulanish saqlanib qoladi)"
}

$natija = (& $ADB -s $QURILMA install -r -g "$APK" | Out-String)
if ($natija -notmatch "Success") {
    if ($natija -match "INSTALL_FAILED_UPDATE_INCOMPATIBLE|signatures do not match") {
        Ogoh "Telefondagi eski ilova boshqa kalit bilan imzolangan."
        Ogoh "DIQQAT: o'chirilsa ilovaning sozlamalari va ulanishi yo'qoladi."
        if (HaMi "Eski ilova o'chirilib, yangisi o'rnatilsinmi?") {
            & $ADB -s $QURILMA uninstall $PAKET | Out-Null
            $natija = (& $ADB -s $QURILMA install -r -g "$APK" | Out-String)
        } else {
            Toxta "O'rnatish bekor qilindi."
        }
    } elseif ($natija -match "Unknown option") {
        $natija = (& $ADB -s $QURILMA install -r "$APK" | Out-String)
    }
}
if ($natija -notmatch "Success") {
    Write-Host $natija
    Toxta "Ilova o'rnatilmadi."
}
Yaxshi "Ilova o'rnatildi (v$ilovaVersiya)"

# ------------------------------------------------------- 7) ruxsatlar
Sarlavha "7. Ruxsatlar va cheklovlar"

foreach ($ruxsat in $RUXSATLAR) {
    $chiqish = Shell "pm grant $PAKET $($ruxsat.nom)"
    $berildi = (Shell "dumpsys package $PAKET | grep $($ruxsat.nom)") -match "granted=true"
    if ($berildi) { Yaxshi $ruxsat.izoh }
    elseif ($chiqish -match "not a changeable permission type|has not requested permission") {
        Oddiy "$($ruxsat.izoh) - bu Android versiyada kerak emas"
    } else { Ogoh "$($ruxsat.izoh) - berilmadi, ilovada qo'lda bering" }
}

Shell "dumpsys deviceidle whitelist +$PAKET" | Out-Null
if ((Shell "dumpsys deviceidle whitelist") -match [regex]::Escape($PAKET)) {
    Yaxshi "Batareya tejash cheklovidan chiqarildi"
} else {
    Ogoh "Batareya cheklovini olib bo'lmadi - ilovada 'Ruxsat berish' ni bosing"
}

if ((Son $sdk) -ge 28) {
    Shell "am set-standby-bucket $PAKET active" | Out-Null
    Yaxshi "Ilova 'faol' guruhga qo'yildi"
}
Shell "cmd appops set $PAKET RUN_IN_BACKGROUND allow" | Out-Null
Shell "cmd appops set $PAKET RUN_ANY_IN_BACKGROUND allow" | Out-Null
Yaxshi "Fonda ishlashga ruxsat berildi"

# Android: 30 daqiqada 30 tadan ko'p SMS jo'natilsa ekranda oyna chiqadi
# va telefon qarovsiz bo'lsa jo'natish to'xtab qoladi.
$chegara = Son (Shell "settings get global sms_outgoing_check_max_count")
if ($chegara -ge 200) {
    Yaxshi "SMS chegarasi yetarli ($chegara ta / 30 daqiqa)"
} elseif (HaMi "SMS chegarasi 200 ta ga oshirilsinmi? (ko'p SMS bir yo'la ketishi uchun)") {
    Shell "settings put global sms_outgoing_check_max_count 200" | Out-Null
    if ((Son (Shell "settings get global sms_outgoing_check_max_count")) -ge 200) {
        Yaxshi "SMS chegarasi 200 ta ga oshirildi"
    } else {
        Ogoh "Chegarani o'zgartirib bo'lmadi (ba'zi telefonlar ruxsat bermaydi)"
    }
}

# ---------------------------------------------------- 8) saytga ulanish
Sarlavha "8. Saytga ulanish"

if (-not $manzil) {
    $manzilFayl = Join-Path $SAYT "tailscale_manzil.txt"
    if (Test-Path $manzilFayl) { $manzil = (Get-Content $manzilFayl -Raw).Trim() }
}

if (-not $manzil) {
    Ogoh "Sayt manzili aniqlanmadi - ulanish o'tkazib yuborildi."
    Oddiy "Ilovada sozlamalarga kirib manzilni qo'lda yozing."
} else {
    Oddiy "Sayt manzili: $manzil"

    # Server ishlayaptimi
    $ishlayapti = $false
    try {
        Invoke-WebRequest -Uri "$manzil/kirish/" -TimeoutSec 8 -UseBasicParsing | Out-Null
        $ishlayapti = $true
    } catch { $ishlayapti = $false }

    if (-not $ishlayapti) {
        Oddiy "Server ishlamayapti - ishga tushirilmoqda..."
        Start-Process -FilePath (Join-Path $SAYT "Server.bat") -WindowStyle Hidden
        for ($i = 0; $i -lt 15; $i++) {
            Start-Sleep -Seconds 2
            try {
                Invoke-WebRequest -Uri "$manzil/kirish/" -TimeoutSec 5 -UseBasicParsing | Out-Null
                $ishlayapti = $true
                break
            } catch { }
        }
    }

    if (-not $ishlayapti) {
        Ogoh "Saytga ulanib bo'lmadi. Ish stolidagi 'Dasturga kirish' ni bosing"
        Oddiy "va shu skriptni qaytadan ishga tushiring."
    } else {
        Yaxshi "Sayt javob bermoqda"

        # Ulanish kodi saytning o'zida yaratiladi - qo'lda ko'chirish kerak emas
        $kodChiqish = Django "from sms.models import UlanishKodi; print('KOD=' + UlanishKodi.yarat().kod)"
        $kod = ""
        if ($kodChiqish -match "KOD=(\d{12})") { $kod = $Matches[1] }

        if (-not $kod) {
            Ogoh "Ulanish kodi yaratilmadi."
            Oddiy "Saytda 'Xabarnoma' bo'limi yoqilganmi, tekshiring"
            Oddiy "(config\settings.py -> SMS_ESLATMA_YOQILGAN = True)."
        } else {
            Oddiy ("Ulanish kodi: " + ($kod -replace '(\d{4})(\d{4})(\d{4})', '$1 $2 $3'))
            Shell "am start -n $PAKET/.MainActivity --es manzil '$manzil' --es kod '$kod'" | Out-Null
            Yaxshi "Manzil va kod telefonga uzatildi"

            Write-Host ""
            Ogoh "TELEFON EKRANIGA QARANG - 'Ulanish' tugmasini bosing."
            Oddiy "Oynada qaysi saytga ulanayotganingiz yoziladi (xavfsizlik uchun)."

            # Aynan shu kod ishlatilganini kutamiz - qurilma oldin ulangan
            # bo'lsa ham "ulandi" deb yolg'on ko'rsatmasligi uchun
            $tekshir = "from sms.models import UlanishKodi" +
                       "`nk = UlanishKodi.objects.filter(kod='$kod').first()" +
                       "`nif k and k.ishlatilgan:" +
                       "`n    print('ULANDI=' + (k.qurilma.nomi if k.qurilma else '?') + ' | SIM: ' + str(k.qurilma.simlar.count() if k.qurilma else 0))" +
                       "`nelse:" +
                       "`n    print('KUTMOQDA')"

            $ulandi = $false
            for ($i = 0; $i -lt 60; $i++) {
                Start-Sleep -Seconds 3
                $javob = Django $tekshir
                if ($javob -match "ULANDI=(.+)") {
                    Oddiy ("Saytda: " + $Matches[1].Trim())
                    $ulandi = $true
                    break
                }
            }
            if ($ulandi) { Yaxshi "QURILMA SAYTGA ULANDI" }
            else { Ogoh "Ulanish tasdiqlanmadi - telefonda 'Ulanish' bosilganmi?" }
        }
    }
}

# ------------------------------------------------------------- yakun
Write-Host ""
Write-Host "  ===================================================" -ForegroundColor Green
Write-Host "    TAYYOR" -ForegroundColor Green
Write-Host "  ===================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Endi saytda: Xabarnoma -> Qurilmalar" -ForegroundColor White
Write-Host "  Telefon 'Onlayn' bo'lib turishi kerak." -ForegroundColor White
Write-Host ""
Write-Host "  SMS yuborish: Xabarnoma -> Xabarlar -> qurilmani belgilang" -ForegroundColor White
Write-Host "                -> 'Yuborish'" -ForegroundColor White
Write-Host ""

if (-not $Savolsiz) {
    Write-Host "  Yopish uchun Enter ni bosing..." -ForegroundColor DarkGray
    Read-Host | Out-Null
}
