# ============================================================
#  Biologiya kursi - ish stoliga yorliq qo'yish
#
#  Nomlar muhit o'zgaruvchilari orqali keladi (BIO_JOY, BIO_YORLIQ1,
#  BIO_YORLIQ2). Shunday qilinganining sababi: nomlarda apostrof bor
#  ("Serverni to'xtatish"), buyruq satriga to'g'ridan-to'g'ri yozilsa
#  turli kompyuterlarda turlicha o'qilib ketishi mumkin.
#
#  Avval umumiy ish stoli (C:\Users\Public\Desktop) sinaladi - unga
#  yozish uchun administrator huquqi kerak. Bo'lmasa, foydalanuvchining
#  o'z ish stoliga qo'yiladi. Har bir yorliq alohida tekshiriladi.
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

$joylar = @(
    [Environment]::GetFolderPath('CommonDesktopDirectory'),
    [Environment]::GetFolderPath('Desktop')
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

$ws = New-Object -ComObject WScript.Shell


function Ochir($manzil) {
    if (Test-Path -LiteralPath $manzil) {
        Remove-Item -LiteralPath $manzil -Force -ErrorAction SilentlyContinue
        return -not (Test-Path -LiteralPath $manzil)
    }
    return $false
}


function Yorliq-Yarat($papka, $yozuv) {
    $manzil = Join-Path $papka ($yozuv.nom + '.lnk')
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

    if (-not (Test-Path -LiteralPath $manzil)) { throw "fayl paydo bo'lmadi" }
    Unblock-File -LiteralPath $manzil -ErrorAction SilentlyContinue
    return $manzil
}


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
# Kerak bo'lsa foydalanuvchi qo'lda ish stoliga ko'chira oladi
foreach ($yozuv in $nomlar) {
    try { Yorliq-Yarat $joy $yozuv | Out-Null } catch { }
}

exit $xato
