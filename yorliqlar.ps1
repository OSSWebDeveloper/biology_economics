# ============================================================
#  Biologiya kursi - ish stoliga yorliq qo'yish
#
#  Nomlar muhit o'zgaruvchilari orqali keladi (BIO_JOY, BIO_YORLIQ1,
#  BIO_YORLIQ2). Shunday qilinganining sababi: nomlarda apostrof bor
#  ("Serverni to'xtatish"), buyruq satriga to'g'ridan-to'g'ri yozilsa
#  turli kompyuterlarda turlicha o'qilib ketishi mumkin.
#
#  BIO_ISHSTOLI - foydalanuvchining HAQIQIY ish stoli papkasi.
#  ORNATISH.bat uni administrator huquqi so'rashdan OLDIN aniqlab
#  uzatadi. Sababi: UAC boshqa hisob bilan ko'tarilsa, ko'tarilgan
#  jarayon uchun "ish stoli" - o'sha administratorning ish stoli
#  bo'lib qoladi va yorliq foydalanuvchiga ko'rinmaydi. OneDrive
#  ish stolni o'ziga ko'chirgan kompyuterlarda ham shu manzil to'g'ri
#  keladi.
# ============================================================
$ErrorActionPreference = 'Stop'

$joy = $env:BIO_JOY
if (-not $joy) { $joy = 'C:\bio_moliya' }

$nomlar = @(
    @{ nom = $(if ($env:BIO_YORLIQ1) { $env:BIO_YORLIQ1 } else { 'Dasturga kirish' })
       fayl = 'Ishga_tushirish.vbs'
       belgi = 'bio.ico'
       izoh = 'Biologiya kursi - dasturni ochish' },
    @{ nom = $(if ($env:BIO_YORLIQ2) { $env:BIO_YORLIQ2 } else { "Serverni to'xtatish" })
       fayl = 'Toxtatish.vbs'
       belgi = 'bio_stop.ico'
       izoh = 'Biologiya kursi - serverni toxtatish' }
)

# Ish stoli papkalari - birinchisi ustun. Umumiy ish stoli (Public)
# eng oxirida: unga qo'yilgan yorliq ba'zi kompyuterlarda darrov
# ko'rinmaydi, shu sababli faqat zaxira sifatida ishlatiladi.
$joylar = @(
    $env:BIO_ISHSTOLI,
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('CommonDesktopDirectory')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
    ForEach-Object { $_.TrimEnd('') } |
    Select-Object -Unique

# WScript.Shell ba'zi kompyuterlarda siyosat yoki antivirus tomonidan
# o'chirib qo'yiladi. Shunday holatda papkadagi tayyor .lnk fayllari
# ko'chiriladi - ular ham aynan shu manzillarga ishora qiladi.
$ws = $null
try { $ws = New-Object -ComObject WScript.Shell } catch { $ws = $null }
if (-not $ws) {
    Write-Host "    WScript.Shell ishlamadi - tayyor yorliqlar ko'chiriladi."
}


function Ochir($manzil) {
    if (Test-Path -LiteralPath $manzil) {
        Remove-Item -LiteralPath $manzil -Force -ErrorAction SilentlyContinue
        return -not (Test-Path -LiteralPath $manzil)
    }
    return $false
}


function Yorliq-Yarat($papka, $yozuv) {
    $manzil = Join-Path $papka ($yozuv.nom + '.lnk')

    if ($ws) {
        # Eski faylni olib tashlaymiz: internetdan tushgan .lnk "bloklangan"
        # bo'lishi va yangilanmasligi mumkin
        Ochir $manzil | Out-Null

        $l = $ws.CreateShortcut($manzil)
        $l.TargetPath = Join-Path $joy $yozuv.fayl
        $l.WorkingDirectory = $joy
        $belgi = Join-Path $joy $yozuv.belgi
        if (Test-Path -LiteralPath $belgi) { $l.IconLocation = $belgi }
        $l.Description = $yozuv.izoh
        $l.Save()
    } else {
        $manba = Join-Path $joy ($yozuv.nom + '.lnk')
        if (-not (Test-Path -LiteralPath $manba)) {
            throw "tayyor yorliq topilmadi: $manba"
        }
        if ($manba -eq $manzil) { return $manzil }
        Copy-Item -LiteralPath $manba -Destination $manzil -Force
    }

    if (-not (Test-Path -LiteralPath $manzil)) { throw "fayl paydo bo'lmadi" }
    Unblock-File -LiteralPath $manzil -ErrorAction SilentlyContinue
    return $manzil
}


Write-Host ("    Ish stoli: " + ($joylar -join ' | '))

# --- eski nomdagi yorliqlar tozalanadi --------------------------------
foreach ($papka in $joylar) {
    foreach ($eski in @('Biologiya kursi.lnk', 'Dasturni yopish.lnk')) {
        if (Ochir (Join-Path $papka $eski)) {
            Write-Host ("    Eski yorliq olib tashlandi: " + $eski)
        }
    }
}

# --- yorliqlar yaratiladi ---------------------------------------------
$xato = 0
foreach ($yozuv in $nomlar) {
    $qoyilgan = $null
    $sabab = 'ish stoli papkasi topilmadi'

    foreach ($papka in $joylar) {
        try {
            $qoyilgan = Yorliq-Yarat $papka $yozuv
            break
        } catch {
            $sabab = $_.Exception.Message
        }
    }

    if ($qoyilgan) {
        Write-Host ("    [+] " + $qoyilgan)
        # Ikki nusxa ko'rinmasin: boshqa ish stolidagi shu nomli yorliq olinadi
        foreach ($papka in $joylar) {
            $boshqa = Join-Path $papka ($yozuv.nom + '.lnk')
            if ($boshqa -ne $qoyilgan) { Ochir $boshqa | Out-Null }
        }
    } else {
        $xato = $xato + 1
        Write-Host ("    [-] " + $yozuv.nom + " - yaratilmadi: " + $sabab)
    }
}

# --- papkaning o'zida ham nusxasi tursin ------------------------------
# Kerak bo'lsa foydalanuvchi qo'lda ish stoliga ko'chira oladi.
# ($ws bo'lmasa manba ham, nusxa ham shu fayl bo'lib qoladi - o'tkazamiz)
if ($ws) {
    foreach ($yozuv in $nomlar) {
        try { Yorliq-Yarat $joy $yozuv | Out-Null } catch { }
    }
}

# --- ish stolini yangilash --------------------------------------------
# Yangi yorliq darrov ko'rinsin: Explorer'ga o'zgarish haqida xabar beramiz
try {
    Add-Type -Namespace Bio -Name Qobiq -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("shell32.dll")]
public static extern void SHChangeNotify(int eventId, uint flags, System.IntPtr item1, System.IntPtr item2);
'@
    [Bio.Qobiq]::SHChangeNotify(0x08000000, 0x0000, [System.IntPtr]::Zero, [System.IntPtr]::Zero)
} catch { }

exit $xato
