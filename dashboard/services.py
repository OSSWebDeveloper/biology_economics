"""Moliyaviy statistika."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce

from payments.models import Tranzaksiya, Usul
from payments.services import (
    NOL,
    PUL,
    balans_bilan,
    keyingi_oy_boshi,
    oldingi_oy_boshi,
    oy_boshi,
    oy_nomi,
    oy_oxiri,
)
from staff.models import XodimTranzaksiya
from students.models import Guruh, Oquvchi

BERILGAN_TURLAR = [XodimTranzaksiya.Tur.AVANS, XodimTranzaksiya.Tur.OYLIK]


NOL_QIYMAT = Value(NOL, output_field=PUL)


def _yigindi(qs, maydon="summa"):
    return qs.aggregate(s=Coalesce(Sum(maydon), NOL_QIYMAT))["s"] or NOL


def davr_chegarasi(kod, boshi=None, oxiri=None):
    """Tanlangan davr uchun (boshlanish, tugash, nom) qaytaradi."""
    bugun = date.today()
    if kod == "bugun":
        return bugun, bugun, "Bugun"
    if kod == "hafta":
        b = bugun - timedelta(days=bugun.weekday())
        return b, bugun, "Shu hafta"
    if kod == "otgan_oy":
        o = oldingi_oy_boshi(bugun)
        return o, oy_oxiri(o), oy_nomi(o)
    if kod == "yil":
        return date(bugun.year, 1, 1), bugun, f"{bugun.year}-yil"
    if kod == "hammasi":
        return None, None, "Butun davr"
    if kod == "tanlangan" and (boshi or oxiri):
        nom = f"{boshi or '...'} - {oxiri or '...'}"
        return boshi, oxiri, nom
    o = oy_boshi(bugun)
    return o, oy_oxiri(o), oy_nomi(o)


def _davr_ichida(qs, boshi, oxiri):
    if boshi:
        qs = qs.filter(sana__gte=boshi)
    if oxiri:
        qs = qs.filter(sana__lte=oxiri)
    return qs


def moliya_hisoboti(boshi, oxiri):
    """Davr bo'yicha kirim-chiqim hisoboti."""
    tolovlar = _davr_ichida(
        Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV), boshi, oxiri
    )
    qaytarilgan = _davr_ichida(
        Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.QAYTARISH), boshi, oxiri
    )
    hisoblangan = _davr_ichida(
        Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.HISOB), boshi, oxiri
    )
    chegirmalar = _davr_ichida(
        Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.CHEGIRMA), boshi, oxiri
    )
    xodim_tolovlari = _davr_ichida(
        XodimTranzaksiya.objects.filter(tur__in=BERILGAN_TURLAR), boshi, oxiri
    )

    kirim_naqd = _yigindi(tolovlar.filter(usul=Usul.NAQD))
    kirim_plastik = _yigindi(tolovlar.filter(usul=Usul.PLASTIK))
    kirim = kirim_naqd + kirim_plastik

    chiqim_naqd = _yigindi(xodim_tolovlari.filter(usul=Usul.NAQD))
    chiqim_plastik = _yigindi(xodim_tolovlari.filter(usul=Usul.PLASTIK))
    qaytarilgan_summa = _yigindi(qaytarilgan)
    chiqim = chiqim_naqd + chiqim_plastik + qaytarilgan_summa

    hisoblangan_summa = _yigindi(hisoblangan)
    yigilish = (kirim / hisoblangan_summa * 100) if hisoblangan_summa else NOL

    return {
        "kirim": kirim,
        "kirim_naqd": kirim_naqd,
        "kirim_plastik": kirim_plastik,
        "kirim_soni": tolovlar.count(),
        "chiqim": chiqim,
        "chiqim_naqd": chiqim_naqd,
        "chiqim_plastik": chiqim_plastik,
        "qaytarilgan": qaytarilgan_summa,
        "avans": _yigindi(xodim_tolovlari.filter(tur=XodimTranzaksiya.Tur.AVANS)),
        "oylik": _yigindi(xodim_tolovlari.filter(tur=XodimTranzaksiya.Tur.OYLIK)),
        "hisoblangan": hisoblangan_summa,
        "chegirma": _yigindi(chegirmalar),
        "yigilish_foizi": round(float(yigilish), 1),
        "sof_foyda": kirim - chiqim,
    }


def qarzdorlik_holati():
    """Hozirgi umumiy qarz / oldindan to'lov holati."""
    oquvchilar = balans_bilan(Oquvchi.objects.filter(faol=True))
    qarz = NOL
    oldindan = NOL
    qarzdorlar = 0
    oldindanlar = 0
    for balans in oquvchilar.values_list("balans_summa", flat=True):
        if balans < 0:
            qarz += -balans
            qarzdorlar += 1
        elif balans > 0:
            oldindan += balans
            oldindanlar += 1

    xodim_qarzi = NOL
    from staff.services import qoldiq_bilan
    from staff.models import Xodim
    for qoldiq in qoldiq_bilan(Xodim.objects.filter(faol=True)).values_list(
        "qoldiq_summa", flat=True
    ):
        if qoldiq > 0:
            xodim_qarzi += qoldiq

    return {
        "qarz": qarz,
        "qarzdorlar": qarzdorlar,
        "oldindan": oldindan,
        "oldindanlar": oldindanlar,
        "xodim_qarzi": xodim_qarzi,
    }


def oylik_dinamika(oylar_soni=12):
    """Oxirgi N oy uchun kirim/chiqim jadvali (grafik uchun)."""
    bugun = date.today()
    davr = oy_boshi(bugun)
    for _ in range(oylar_soni - 1):
        davr = oldingi_oy_boshi(davr)

    natija = []
    joriy = davr
    while joriy <= oy_boshi(bugun):
        tugash = oy_oxiri(joriy)
        kirim = _yigindi(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV,
                                       sana__gte=joriy, sana__lte=tugash)
        )
        chiqim = _yigindi(
            XodimTranzaksiya.objects.filter(tur__in=BERILGAN_TURLAR,
                                            sana__gte=joriy, sana__lte=tugash)
        )
        natija.append({
            "davr": joriy,
            "nom": oy_nomi(joriy),
            "qisqa": f"{joriy.month:02d}.{str(joriy.year)[2:]}",
            "kirim": kirim,
            "chiqim": chiqim,
            "foyda": kirim - chiqim,
        })
        joriy = keyingi_oy_boshi(joriy)

    eng_katta = max([max(q["kirim"], q["chiqim"]) for q in natija] or [NOL]) or Decimal(1)
    for qator in natija:
        qator["kirim_foiz"] = round(float(qator["kirim"] / eng_katta * 100), 1)
        qator["chiqim_foiz"] = round(float(qator["chiqim"] / eng_katta * 100), 1)
    return natija


def guruhlar_kesimi(boshi, oxiri):
    natija = []
    for guruh in Guruh.objects.filter(faol=True):
        tolov = _yigindi(_davr_ichida(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV, oquvchi__guruh=guruh),
            boshi, oxiri))
        hisob = _yigindi(_davr_ichida(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.HISOB, oquvchi__guruh=guruh),
            boshi, oxiri))
        natija.append({
            "guruh": guruh,
            "oquvchilar": guruh.faol_oquvchilar_soni,
            "hisoblangan": hisob,
            "tolangan": tolov,
            "farq": tolov - hisob,
        })
    return sorted(natija, key=lambda q: q["tolangan"], reverse=True)


def kartalar_kesimi(boshi, oxiri):
    qs = _davr_ichida(
        Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV, usul=Usul.PLASTIK),
        boshi, oxiri,
    )
    return (qs.values("karta__nomi", "karta__raqam", "karta_raqami")
              .annotate(summa=Sum("summa"), soni=Count("id"))
              .order_by("-summa"))


def top_qarzdorlar(soni=8):
    qs = balans_bilan(Oquvchi.objects.filter(faol=True)).filter(balans_summa__lt=0)
    return qs.order_by("balans_summa")[:soni]


def bugungi_holat():
    bugun = date.today()
    oy = oy_boshi(bugun)
    return {
        "bugun_kirim": _yigindi(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV, sana=bugun)),
        "oy_kirim": _yigindi(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV,
                                       sana__gte=oy, sana__lte=bugun)),
        "oy_chiqim": _yigindi(
            XodimTranzaksiya.objects.filter(tur__in=BERILGAN_TURLAR,
                                            sana__gte=oy, sana__lte=bugun)),
        "faol_oquvchilar": Oquvchi.objects.filter(faol=True).count(),
        "yangi_oquvchilar": Oquvchi.objects.filter(
            boshlangan_sana__gte=oy, boshlangan_sana__lte=bugun).count(),
        "oy_nomi": oy_nomi(oy),
    }
