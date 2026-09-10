"""Kurs to'lovlarini hisoblash mantiqi.

Asosiy qoida (klient talabi):
  * Oylik kurs puli o'sha oydagi kunlar soniga bo'linadi -> kunlik narx.
  * O'quvchi oyning o'rtasida kelsa, kelgan sanasidan keyingi oyning
    1-sanasigacha bo'lgan kunlar uchun to'laydi.
  * 1-sanadan boshlab yangi to'liq sikl (to'liq oylik summa) boshlanadi.
"""
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce

from students.models import Oquvchi

from .models import Tranzaksiya

PUL = DecimalField(max_digits=14, decimal_places=2)
NOL = Decimal("0")

OY_NOMLARI = ["yanvar", "fevral", "mart", "aprel", "may", "iyun",
              "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


# --------------------------------------------------------------------------
# Sana yordamchilari
# --------------------------------------------------------------------------

def oy_boshi(sana):
    return date(sana.year, sana.month, 1)


def oydagi_kunlar(sana):
    return monthrange(sana.year, sana.month)[1]


def oy_oxiri(sana):
    return date(sana.year, sana.month, oydagi_kunlar(sana))


def keyingi_oy_boshi(sana):
    return oy_oxiri(sana) + timedelta(days=1)


def oldingi_oy_boshi(sana):
    return oy_boshi(oy_boshi(sana) - timedelta(days=1))


def oy_nomi(sana):
    return f"{OY_NOMLARI[sana.month - 1]} {sana.year}"


def pulga_yaxlitla(qiymat):
    """So'mni butun songa yaxlitlaydi (tiyinsiz)."""
    return Decimal(qiymat).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------
# Hisoblash
# --------------------------------------------------------------------------

def kunlik_narx(oylik_toluv, davr):
    """Bir kunlik narx = oylik to'lov / shu oydagi kunlar soni."""
    kunlar = oydagi_kunlar(davr)
    if not kunlar:
        return NOL
    return Decimal(oylik_toluv) / Decimal(kunlar)


def davr_summasi(oquvchi, davr, tugash_sana=None):
    """`davr` (oyning 1-sanasi) uchun hisoblanadigan summa.

    Qaytaradi: (summa, kunlar_soni)
    """
    oylik = Decimal(oquvchi.amaldagi_oylik or 0)
    if oylik <= 0:
        return NOL, 0

    kunlar_oyda = oydagi_kunlar(davr)
    oyning_oxiri = oy_oxiri(davr)

    boshlanish = max(oquvchi.boshlangan_sana, davr)
    tugash = tugash_sana or oquvchi.chiqarilgan_sana or oyning_oxiri
    tugash = min(tugash, oyning_oxiri)

    if tugash < boshlanish:
        return NOL, 0

    kunlar = (tugash - boshlanish).days + 1
    if kunlar >= kunlar_oyda:
        return pulga_yaxlitla(oylik), kunlar_oyda
    return pulga_yaxlitla(kunlik_narx(oylik, davr) * kunlar), kunlar


def kerakli_davrlar(oquvchi, sanagacha=None):
    """O'quvchi uchun hisob ochilishi kerak bo'lgan oylar ro'yxati."""
    sanagacha = sanagacha or date.today()
    boshi = oy_boshi(oquvchi.boshlangan_sana)

    chegara = sanagacha
    if not oquvchi.faol:
        chegara = min(chegara, oquvchi.chiqarilgan_sana or sanagacha)
    oxirgi = oy_boshi(chegara)

    davrlar = []
    joriy = boshi
    while joriy <= oxirgi:
        davrlar.append(joriy)
        joriy = keyingi_oy_boshi(joriy)
    return davrlar


def _hisob_yozuvi(oquvchi, davr):
    summa, kunlar = davr_summasi(oquvchi, davr)
    if summa <= 0:
        return None
    toliq = kunlar >= oydagi_kunlar(davr)
    izoh = oy_nomi(davr) + (" - to'liq oy" if toliq else f" - {kunlar} kun")
    return Tranzaksiya(
        oquvchi=oquvchi,
        tur=Tranzaksiya.Tur.HISOB,
        summa=summa,
        sana=max(davr, oquvchi.boshlangan_sana),
        davr=davr,
        kunlar=kunlar,
        izoh=izoh,
    )


def hisoblarni_yarat(oquvchi, sanagacha=None):
    """Bitta o'quvchi uchun yetishmayotgan oylik hisoblarni ochadi."""
    mavjud = set(
        Tranzaksiya.objects.filter(oquvchi=oquvchi, tur=Tranzaksiya.Tur.HISOB)
        .values_list("davr", flat=True)
    )
    yangilar = []
    for davr in kerakli_davrlar(oquvchi, sanagacha):
        if davr in mavjud:
            continue
        yozuv = _hisob_yozuvi(oquvchi, davr)
        if yozuv:
            yangilar.append(yozuv)
    if yangilar:
        Tranzaksiya.objects.bulk_create(yangilar, ignore_conflicts=True)
    return len(yangilar)


def barcha_hisoblarni_yangila(sanagacha=None):
    """Barcha o'quvchilar uchun yetishmayotgan hisoblarni ochadi (idempotent)."""
    sanagacha = sanagacha or date.today()
    mavjud = defaultdict(set)
    for oquvchi_id, davr in Tranzaksiya.objects.filter(
        tur=Tranzaksiya.Tur.HISOB
    ).values_list("oquvchi_id", "davr"):
        mavjud[oquvchi_id].add(davr)

    yangilar = []
    for oquvchi in Oquvchi.objects.all():
        for davr in kerakli_davrlar(oquvchi, sanagacha):
            if davr in mavjud[oquvchi.pk]:
                continue
            yozuv = _hisob_yozuvi(oquvchi, davr)
            if yozuv:
                yangilar.append(yozuv)
    if yangilar:
        Tranzaksiya.objects.bulk_create(yangilar, ignore_conflicts=True)
    return len(yangilar)


def oyni_qayta_hisobla(oquvchi, davr, tugash_sana):
    """Chiqarilgan o'quvchining oxirgi oyini kunlab qayta hisoblaydi."""
    hisob = Tranzaksiya.objects.filter(
        oquvchi=oquvchi, tur=Tranzaksiya.Tur.HISOB, davr=davr
    ).first()
    summa, kunlar = davr_summasi(oquvchi, davr, tugash_sana=tugash_sana)

    if hisob is None:
        if summa > 0:
            yozuv = _hisob_yozuvi(oquvchi, davr)
            if yozuv:
                yozuv.summa, yozuv.kunlar = summa, kunlar
                yozuv.izoh = f"{oy_nomi(davr)} - {kunlar} kun (chiqarilgan)"
                yozuv.save()
        return summa

    if summa <= 0:
        hisob.delete()
        return NOL

    hisob.summa = summa
    hisob.kunlar = kunlar
    hisob.izoh = f"{oy_nomi(davr)} - {kunlar} kun (chiqarilgan)"
    hisob.save(update_fields=["summa", "kunlar", "izoh"])
    return summa


# --------------------------------------------------------------------------
# Balans
# --------------------------------------------------------------------------

MUSBAT_TURLAR = [Tranzaksiya.Tur.TOLOV, Tranzaksiya.Tur.CHEGIRMA, Tranzaksiya.Tur.QARZ]
MANFIY_TURLAR = [Tranzaksiya.Tur.HISOB, Tranzaksiya.Tur.QAYTARISH]


def balans_ifodasi(prefiks="tranzaksiyalar"):
    """QuerySet uchun balans annotatsiyasi."""
    return Coalesce(
        Sum(
            Case(
                When(**{f"{prefiks}__tur__in": MUSBAT_TURLAR}, then=F(f"{prefiks}__summa")),
                When(**{f"{prefiks}__tur__in": MANFIY_TURLAR}, then=-F(f"{prefiks}__summa")),
                default=Value(NOL),
                output_field=PUL,
            )
        ),
        Value(NOL),
        output_field=PUL,
    )


def balans_bilan(queryset):
    return queryset.annotate(balans_summa=balans_ifodasi())


def oquvchi_balansi(oquvchi):
    natija = Tranzaksiya.objects.filter(oquvchi=oquvchi).aggregate(
        b=Coalesce(
            Sum(
                Case(
                    When(tur__in=MUSBAT_TURLAR, then=F("summa")),
                    When(tur__in=MANFIY_TURLAR, then=-F("summa")),
                    default=Value(NOL),
                    output_field=PUL,
                )
            ),
            Value(NOL),
            output_field=PUL,
        )
    )["b"]
    return natija or NOL


def balans_holati(balans):
    """Balansga qarab holat: qarzdor / oldindan to'langan / toza."""
    balans = Decimal(balans or 0)
    if balans < 0:
        return {"kod": "qarzdor", "nom": "Qarzdor", "rang": "qizil", "summa": -balans}
    if balans > 0:
        return {"kod": "oldindan", "nom": "Oldindan to'langan", "rang": "yashil", "summa": balans}
    return {"kod": "toza", "nom": "Qarzi yo'q", "rang": "kulrang", "summa": NOL}


def holat_filtri(queryset, holat):
    """Ro'yxatni to'lov holati bo'yicha filtrlash (balans_bilan() dan keyin)."""
    if holat == "qarzdor":
        return queryset.filter(balans_summa__lt=0)
    if holat == "oldindan":
        return queryset.filter(balans_summa__gt=0)
    if holat == "toza":
        return queryset.filter(balans_summa=0)
    return queryset
