"""Xodimlar oyligini hisoblash (o'quvchilar bilan bir xil kunlab bo'lish qoidasi)."""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import Case, F, Sum, Value, When
from django.db.models.functions import Coalesce

from payments.services import (
    NOL,
    PUL,
    keyingi_oy_boshi,
    oy_boshi,
    oy_nomi,
    oy_oxiri,
    oydagi_kunlar,
    pulga_yaxlitla,
)

from .models import Xodim, XodimTranzaksiya


def maosh_summasi(xodim, davr, tugash_sana=None):
    """`davr` oyi uchun hisoblanadigan maosh: (summa, kunlar)."""
    oylik = Decimal(xodim.oylik_maosh or 0)
    if oylik <= 0:
        return NOL, 0

    kunlar_oyda = oydagi_kunlar(davr)
    oyning_oxiri = oy_oxiri(davr)

    boshlanish = max(xodim.ishga_kirgan_sana, davr)
    tugash = tugash_sana or xodim.ishdan_ketgan_sana or oyning_oxiri
    tugash = min(tugash, oyning_oxiri)

    if tugash < boshlanish:
        return NOL, 0

    kunlar = (tugash - boshlanish).days + 1
    if kunlar >= kunlar_oyda:
        return pulga_yaxlitla(oylik), kunlar_oyda
    return pulga_yaxlitla(oylik / Decimal(kunlar_oyda) * kunlar), kunlar


def kerakli_davrlar(xodim, sanagacha=None):
    sanagacha = sanagacha or date.today()
    chegara = sanagacha
    if not xodim.faol:
        chegara = min(chegara, xodim.ishdan_ketgan_sana or sanagacha)

    davrlar = []
    joriy = oy_boshi(xodim.ishga_kirgan_sana)
    oxirgi = oy_boshi(chegara)
    while joriy <= oxirgi:
        davrlar.append(joriy)
        joriy = keyingi_oy_boshi(joriy)
    return davrlar


def _hisob_yozuvi(xodim, davr):
    summa, kunlar = maosh_summasi(xodim, davr)
    if summa <= 0:
        return None
    toliq = kunlar >= oydagi_kunlar(davr)
    izoh = oy_nomi(davr) + (" oyligi" if toliq else f" - {kunlar} kun")
    return XodimTranzaksiya(
        xodim=xodim,
        tur=XodimTranzaksiya.Tur.HISOB,
        summa=summa,
        sana=max(davr, xodim.ishga_kirgan_sana),
        davr=davr,
        kunlar=kunlar,
        izoh=izoh,
    )


def maoshlarni_yangila(sanagacha=None):
    """Barcha xodimlar uchun yetishmayotgan oylik hisoblarini ochadi."""
    sanagacha = sanagacha or date.today()
    mavjud = defaultdict(set)
    for xodim_id, davr in XodimTranzaksiya.objects.filter(
        tur=XodimTranzaksiya.Tur.HISOB
    ).values_list("xodim_id", "davr"):
        mavjud[xodim_id].add(davr)

    yangilar = []
    for xodim in Xodim.objects.all():
        for davr in kerakli_davrlar(xodim, sanagacha):
            if davr in mavjud[xodim.pk]:
                continue
            yozuv = _hisob_yozuvi(xodim, davr)
            if yozuv:
                yangilar.append(yozuv)
    if yangilar:
        XodimTranzaksiya.objects.bulk_create(yangilar, ignore_conflicts=True)
    return len(yangilar)


MUSBAT_TURLAR = [XodimTranzaksiya.Tur.HISOB, XodimTranzaksiya.Tur.BONUS]
MANFIY_TURLAR = [XodimTranzaksiya.Tur.AVANS, XodimTranzaksiya.Tur.OYLIK,
                 XodimTranzaksiya.Tur.JARIMA]


def qoldiq_ifodasi(prefiks="tranzaksiyalar"):
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


def qoldiq_bilan(queryset):
    return queryset.annotate(qoldiq_summa=qoldiq_ifodasi())


def xodim_qoldigi(xodim):
    natija = XodimTranzaksiya.objects.filter(xodim=xodim).aggregate(
        q=Coalesce(
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
    )["q"]
    return natija or NOL


def qoldiq_holati(qoldiq):
    qoldiq = Decimal(qoldiq or 0)
    if qoldiq > 0:
        return {"kod": "qarzimiz", "nom": "To'lanishi kerak", "rang": "qizil", "summa": qoldiq}
    if qoldiq < 0:
        return {"kod": "ortiqcha", "nom": "Ortiqcha avans", "rang": "sariq", "summa": -qoldiq}
    return {"kod": "toza", "nom": "Hisob-kitob qilingan", "rang": "yashil", "summa": NOL}


def joriy_oy_avansi(xodim, davr=None):
    """Shu oyda xodimga berilgan avans summasi."""
    davr = davr or oy_boshi(date.today())
    natija = XodimTranzaksiya.objects.filter(
        xodim=xodim, tur=XodimTranzaksiya.Tur.AVANS,
        sana__gte=davr, sana__lte=oy_oxiri(davr),
    ).aggregate(s=Coalesce(Sum("summa"), Value(NOL), output_field=PUL))["s"]
    return natija or NOL
