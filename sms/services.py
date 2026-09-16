"""Oylik to'lov eslatmasi: navbat tayyorlash, qurilmalarga taqsimlash.

Qoida (klient talabi):
  * Har oyning 1-sanasida QARZDOR o'quvchilarning ota-onasiga eslatma
    NAVBATGA yoziladi - lekin o'z-o'zidan jo'natilmaydi.
  * Admin "Xabarlar" bo'limida qaysi qurilma va qaysi SIM kartalardan
    yuborishni belgilab, "Yuborish" ni bosadi. Shundan keyingina xabarlar
    tanlangan kanallarga TENG bo'linadi va telefonlar ularni olib jo'natadi.
  * Kimga yuborilishi `SMS_KIMGA` sozlamasidan: otaga / onaga / ikkalasiga.
  * Bir o'quvchi uchun bir oyda bitta xabar (bazadagi cheklov bilan
    kafolatlanadi), shuning uchun navbat necha marta tayyorlansa ham
    takror SMS ketmaydi.
"""
import re
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from payments.services import (
    OY_NOMLARI,
    balans_bilan,
    barcha_hisoblarni_yangila,
    oy_boshi,
)
from students.models import Oquvchi

from . import sozlamalar
from .models import Bildirishnoma, Qurilma, SimKarta, SmsXabar, UlanishKodi


# --------------------------------------------------------------------------
# Telefon raqami
# --------------------------------------------------------------------------

def raqamni_tozala(raqam):
    """Har xil ko'rinishdagi raqamni +998XXXXXXXXX ga keltiradi.

    Noto'g'ri yoki to'liqmas raqamdan bo'sh satr qaytadi - bunday raqamga
    xabar yozilmaydi.
    """
    raqamlar = re.sub(r"\D", "", raqam or "")
    if len(raqamlar) == 9:                                   # 901234567
        return "+998" + raqamlar
    if len(raqamlar) == 12 and raqamlar.startswith("998"):   # 998901234567
        return "+" + raqamlar
    if len(raqamlar) == 10 and raqamlar[0] in "08":          # 8901234567
        return "+998" + raqamlar[1:]
    return ""


def qabul_qiluvchilar(oquvchi, kimga=None):
    """Shu o'quvchi bo'yicha kimga xabar ketishi: [(qabul_qiluvchi, telefon)]."""
    kimga = kimga or sozlamalar.kimga()
    juftlar = []
    if kimga in ("ota", "ikkalasi"):
        juftlar.append((SmsXabar.Qabul.OTA, oquvchi.ota_telefon))
    if kimga in ("ona", "ikkalasi"):
        juftlar.append((SmsXabar.Qabul.ONA, oquvchi.ona_telefon))

    natija = []
    for qabul, raqam in juftlar:
        tozalangan = raqamni_tozala(raqam)
        if tozalangan:
            natija.append((qabul, tozalangan))
    return natija


# --------------------------------------------------------------------------
# Xabar matni
# --------------------------------------------------------------------------

def summani_formatla(summa):
    """450000 -> "450 000" (SMS uchun oddiy probel bilan)."""
    butun = int(Decimal(summa or 0).quantize(Decimal("1")))
    return f"{butun:,}".replace(",", " ")


def xabar_matni(oquvchi, qarz, qabul_qiluvchi="", davr=None):
    """Andozadagi o'rinlarni to'ldiradi.

    Andozada ishlatsa bo'ladigan o'rinlar:
      {oquvchi} {ism} {familiya} {qarz} {kurs} {oy} {oldingi_oy}
    """
    davr = davr or oy_boshi(date.today())
    oldingi = oy_boshi(davr - timedelta(days=1))
    return sozlamalar.matn(qabul_qiluvchi).format(
        oquvchi=oquvchi.toliq_ism,
        ism=oquvchi.ism,
        familiya=oquvchi.familiya,
        qarz=summani_formatla(qarz),
        kurs=sozlamalar.kurs_nomi(),
        oy=OY_NOMLARI[davr.month - 1],
        oldingi_oy=OY_NOMLARI[oldingi.month - 1],
    )


def sms_bolaklari(matn):
    """Matn nechta SMS bo'lib ketishini taxminlaydi (lotin harflar -> 160 belgi)."""
    uzunlik = len(matn)
    if uzunlik <= 160:
        return 1
    return (uzunlik + 152) // 153


# --------------------------------------------------------------------------
# Navbat tayyorlash
# --------------------------------------------------------------------------

def qarzdorlar():
    """Qarzi `SMS_ENG_KAM_QARZ` dan kam bo'lmagan faol o'quvchilar."""
    chegara = -Decimal(sozlamalar.eng_kam_qarz())
    qs = Oquvchi.objects.filter(faol=True, arxiv__isnull=True)
    return (balans_bilan(qs)
            .filter(balans_summa__lte=chegara)
            .order_by("familiya", "ism"))


def _tayyorla(sana, saqla):
    """Navbatga qo'yiladigan xabarlarni yig'adi (kun tekshiruvisiz)."""
    davr = oy_boshi(sana)
    test_raqam = sozlamalar.test_raqam()

    mavjud = set(
        SmsXabar.objects.filter(davr=davr)
        .values_list("oquvchi_id", "qabul_qiluvchi")
    )

    yangilar = []
    for oquvchi in qarzdorlar():
        qarz = -Decimal(oquvchi.balans_summa)
        for qabul, telefon in qabul_qiluvchilar(oquvchi):
            if (oquvchi.pk, qabul) in mavjud:
                continue
            yangilar.append(SmsXabar(
                oquvchi=oquvchi,
                qabul_qiluvchi=qabul,
                telefon=test_raqam or telefon,
                matn=xabar_matni(oquvchi, qarz, qabul, davr),
                davr=davr,
                summa=qarz,
            ))

    if yangilar and saqla:
        SmsXabar.objects.bulk_create(yangilar, ignore_conflicts=True)
    return yangilar


def vaqti_keldimi(sana, majburiy=False):
    """Bugun navbat tayyorlanadigan kunmi?"""
    if majburiy:
        return True
    kun = sozlamalar.yuborish_kuni()
    return kun <= sana.day <= kun + sozlamalar.kechikish_kuni()


def eslatmalarni_navbatga_qoy(sana=None, majburiy=False):
    """Navbatni tayyorlaydi. Yangi yozilgan xabarlar sonini qaytaradi.

    DIQQAT: bu faqat navbat. SMS lar admin "Yuborish" ni bosgandan keyin
    ketadi (`taqsimla`).
    """
    if not sozlamalar.yoqilgan():
        return 0
    sana = sana or date.today()
    if not vaqti_keldimi(sana, majburiy):
        return 0
    # Qarz raqami to'g'ri bo'lishi uchun avval oylik hisoblar ochilsin.
    barcha_hisoblarni_yangila(sanagacha=sana)
    soni = len(_tayyorla(sana, saqla=True))
    if soni:
        Bildirishnoma.qosh(
            Bildirishnoma.Turi.MALUMOT,
            f"{soni} ta eslatma navbatga tayyorlandi - yuborish uchun qurilma tanlang.",
        )
    return soni


def sinov_royxati(sana=None):
    """Nima yuborilishini ko'rish uchun: bazaga yozmaydi."""
    return _tayyorla(sana or date.today(), saqla=False)


def avtomatik_tekshir():
    """Sayt sahifasi ochilganda chaqiriladi - modul o'chiq bo'lsa tekin qaytadi."""
    if not sozlamalar.yoqilgan():
        return 0
    return eslatmalarni_navbatga_qoy()


# --------------------------------------------------------------------------
# Qurilmani ulash
# --------------------------------------------------------------------------

class UlanishXatosi(Exception):
    pass


@transaction.atomic
def qurilmani_ulash(kod, malumot):
    """12 xonalik kod bilan telefonni saytga ulaydi.

    `malumot` - ilova yuborgan lug'at: qurilma_id, nomi, model, android,
    ilova_versiya, simlar[].

    Qaytaradi: (qurilma, kalit). Xato bo'lsa `UlanishXatosi` ko'taradi.
    """
    raqamlar = re.sub(r"\D", "", str(kod or ""))
    if len(raqamlar) != 12:
        raise UlanishXatosi("Kod 12 xonali bo'lishi kerak")

    yozuv = (UlanishKodi.objects
             .select_for_update()
             .filter(kod=raqamlar)
             .first())
    if yozuv is None:
        raise UlanishXatosi("Bunday kod yo'q")
    if yozuv.ishlatilgan is not None:
        raise UlanishXatosi("Bu kod allaqachon ishlatilgan")
    if timezone.now() >= yozuv.amal_qiladi:
        raise UlanishXatosi("Kodning muddati tugagan - saytdan yangisini oling")

    qurilma_id = str(malumot.get("qurilma_id") or "").strip()[:64]
    if not qurilma_id:
        raise UlanishXatosi("Qurilma belgisi yuborilmadi")

    nomi = str(malumot.get("nomi") or "").strip()[:100] or "Telefon"
    kalit = Qurilma.kalit_yarat()

    qurilma, yangimi = Qurilma.objects.get_or_create(
        qurilma_id=qurilma_id,
        defaults={"nomi": nomi, "kalit": kalit},
    )
    qurilma.nomi = nomi
    qurilma.ishlab_chiqaruvchi = str(malumot.get("ishlab_chiqaruvchi") or "").strip()[:60]
    qurilma.model = str(malumot.get("model") or "").strip()[:60]
    qurilma.android = str(malumot.get("android") or "").strip()[:20]
    qurilma.ilova_versiya = str(malumot.get("ilova_versiya") or "").strip()[:20]
    qurilma.kalit = kalit          # qayta ulanishda kalit yangilanadi
    qurilma.faol = True
    qurilma.oxirgi_aloqa = timezone.now()
    qurilma.save()

    simlarni_yangila(qurilma, malumot.get("simlar") or [])

    yozuv.qurilma = qurilma
    yozuv.ishlatilgan = timezone.now()
    yozuv.save(update_fields=["qurilma", "ishlatilgan"])

    Bildirishnoma.qosh(
        Bildirishnoma.Turi.ULANDI,
        f"{qurilma.nomi} saytga ulandi" + ("" if yangimi else " (qayta ulanish)"),
        qurilma,
    )
    return qurilma, kalit


def simlarni_yangila(qurilma, simlar):
    """Ilova yuborgan SIM ro'yxatini bazaga yozadi (tanlangan holatni saqlab)."""
    korilgan = []
    for tartib, sim in enumerate(simlar or []):
        try:
            sim_id = int(sim.get("id"))
        except (TypeError, ValueError):
            continue
        yozuv, _ = SimKarta.objects.update_or_create(
            qurilma=qurilma,
            sim_id=sim_id,
            defaults={
                "nomi": str(sim.get("nomi") or f"SIM {tartib + 1}")[:60],
                "raqam": raqamni_tozala(sim.get("raqam")) or str(sim.get("raqam") or "")[:30],
                "slot": int(sim.get("slot") or tartib),
            },
        )
        korilgan.append(yozuv.pk)

    if korilgan:
        # Telefondan olib tashlangan SIM lar o'chiriladi
        qurilma.simlar.exclude(pk__in=korilgan).delete()
    return qurilma.simlar.count()


def aloqani_belgila(qurilma, batareya=None, ilova_versiya=""):
    """Har bir so'rovda chaqiriladi - qurilma "onlayn" bo'lib turadi."""
    yangilanadi = ["oxirgi_aloqa"]
    qurilma.oxirgi_aloqa = timezone.now()
    if batareya is not None:
        try:
            qurilma.batareya = max(0, min(100, int(batareya)))
            yangilanadi.append("batareya")
        except (TypeError, ValueError):
            pass
    if ilova_versiya and ilova_versiya != qurilma.ilova_versiya:
        qurilma.ilova_versiya = str(ilova_versiya)[:20]
        yangilanadi.append("ilova_versiya")
    qurilma.save(update_fields=yangilanadi)


# --------------------------------------------------------------------------
# Taqsimlash (admin "Yuborish" ni bosganda)
# --------------------------------------------------------------------------

def kanallar_royxati(sim_pklari=None, qurilma_pklari=None):
    """Yuborish uchun tanlangan kanallar: har biri (qurilma, sim) juftligi.

    SIM tanlanmagan qurilma uchun sim = None (telefon standart SIM ni ishlatadi).
    """
    kanallar = []

    if sim_pklari:
        simlar = (SimKarta.objects
                  .filter(pk__in=sim_pklari, faol=True, qurilma__faol=True)
                  .select_related("qurilma")
                  .order_by("qurilma__nomi", "slot"))
        for sim in simlar:
            kanallar.append((sim.qurilma, sim))

    if qurilma_pklari:
        tanlangan_qurilmalar = {q.pk for q, _ in kanallar}
        for qurilma in (Qurilma.objects
                        .filter(pk__in=qurilma_pklari, faol=True)
                        .order_by("nomi")):
            if qurilma.pk not in tanlangan_qurilmalar:
                kanallar.append((qurilma, None))

    return kanallar


@transaction.atomic
def taqsimla(kanallar, xabarlar=None):
    """Navbatdagi xabarlarni kanallarga TENG bo'lib beradi.

    Qaytaradi: {"jami": n, "kanallar": [(qurilma, sim, nechta), ...]}
    """
    if not kanallar:
        return {"jami": 0, "kanallar": []}

    if xabarlar is None:
        xabarlar = list(
            SmsXabar.objects.select_for_update()
            .filter(holat=SmsXabar.Holat.NAVBATDA)
            .order_by("yaratilgan", "id")
        )
    if not xabarlar:
        return {"jami": 0, "kanallar": []}

    hozir = timezone.now()
    sanoq = {i: 0 for i in range(len(kanallar))}

    # Navbatma-navbat (round-robin) - farq ko'pi bilan bitta xabar bo'ladi
    for tartib, xabar in enumerate(xabarlar):
        indeks = tartib % len(kanallar)
        qurilma, sim = kanallar[indeks]
        xabar.qurilma = qurilma
        xabar.sim = sim
        xabar.holat = SmsXabar.Holat.BERILDI
        xabar.berilgan = hozir
        xabar.urinishlar = 0
        xabar.xato_matni = ""
        sanoq[indeks] += 1

    SmsXabar.objects.bulk_update(
        xabarlar, ["qurilma", "sim", "holat", "berilgan", "urinishlar", "xato_matni"]
    )

    natija = [(kanallar[i][0], kanallar[i][1], soni) for i, soni in sanoq.items() if soni]
    tafsilot = ", ".join(
        f"{qurilma.nomi}{' / ' + sim.nomi if sim else ''}: {soni} ta"
        for qurilma, sim, soni in natija
    )
    Bildirishnoma.qosh(
        Bildirishnoma.Turi.YUBORILDI,
        f"{len(xabarlar)} ta xabar yuborishga berildi ({tafsilot})",
    )
    return {"jami": len(xabarlar), "kanallar": natija}


def berilganlarni_bosat(daqiqa=None):
    """Oflayn qurilmada qotib qolgan xabarlarni navbatga qaytaradi.

    Qurilma o'chib qolsa yoki internetdan uzilsa, unga berilgan xabarlar
    abadiy kutib qolmasligi kerak - ular navbatga qaytadi va boshqa
    qurilmaga berilishi mumkin.
    """
    daqiqa = daqiqa or sozlamalar.bosatish_daqiqa()
    chegara = timezone.now() - timedelta(minutes=daqiqa)
    qaytdi = (SmsXabar.objects
              .filter(holat__in=[SmsXabar.Holat.BERILDI, SmsXabar.Holat.OLINDI],
                      berilgan__lt=chegara)
              .update(holat=SmsXabar.Holat.NAVBATDA, qurilma=None, sim=None,
                      berilgan=None, olingan=None))
    if qaytdi:
        Bildirishnoma.qosh(
            Bildirishnoma.Turi.MALUMOT,
            f"{qaytdi} ta xabar qurilmadan qaytarib olindi (uzoq vaqt jo'natilmadi).",
        )
    return qaytdi


# --------------------------------------------------------------------------
# Telefondagi ilova uchun navbat
# --------------------------------------------------------------------------

def qurilma_navbati(qurilma, limit=None):
    """Shu qurilmaga berilgan xabarlar; berilganda "olindi" deb belgilanadi."""
    limit = limit or sozlamalar.bir_martada()
    eskirgan = timezone.now() - timedelta(minutes=SmsXabar.QAYTA_BERISH_DAQIQA)

    qs = (SmsXabar.objects
          .filter(qurilma=qurilma)
          .filter(Q(holat=SmsXabar.Holat.BERILDI)
                  | Q(holat=SmsXabar.Holat.OLINDI, olingan__lt=eskirgan))
          .filter(urinishlar__lt=sozlamalar.urinishlar_chegarasi())
          .select_related("sim")
          .order_by("berilgan", "id"))

    xabarlar = list(qs[:limit])
    if xabarlar:
        hozir = timezone.now()
        for xabar in xabarlar:
            xabar.holat = SmsXabar.Holat.OLINDI
            xabar.olingan = hozir
            xabar.urinishlar += 1
        SmsXabar.objects.bulk_update(xabarlar, ["holat", "olingan", "urinishlar"])
    return xabarlar


def holatni_belgila(xabar_id, holat, xato="", qurilma=None):
    """Ilova jo'natgandan keyin natijani qayd etadi."""
    qs = SmsXabar.objects.filter(pk=xabar_id)
    if qurilma is not None:
        qs = qs.filter(qurilma=qurilma)
    xabar = qs.first()
    if xabar is None:
        return False

    if holat == SmsXabar.Holat.JONATILDI:
        xabar.holat = SmsXabar.Holat.JONATILDI
        xabar.jonatilgan = timezone.now()
        xabar.xato_matni = ""
    else:
        # Urinishlar tugamagan bo'lsa qurilmada qoladi, tugagan bo'lsa - xato.
        tugadi = xabar.urinishlar >= sozlamalar.urinishlar_chegarasi()
        xabar.holat = SmsXabar.Holat.XATO if tugadi else SmsXabar.Holat.BERILDI
        xabar.xato_matni = str(xato or "")[:255]
        if tugadi:
            Bildirishnoma.qosh(
                Bildirishnoma.Turi.XATO,
                f"{xabar.telefon} ({xabar.oquvchi}) - jo'natilmadi: {xabar.xato_matni}",
                xabar.qurilma,
            )

    xabar.save(update_fields=["holat", "jonatilgan", "xato_matni"])
    return True


# --------------------------------------------------------------------------
# Qayta urinish
# --------------------------------------------------------------------------

def qayta_urin(xabar):
    """Jo'natilmagan xabarni qaytadan navbatga qo'yadi.

    Qurilma hali onlayn bo'lsa - o'sha qurilmada qoladi (darhol ketadi),
    aks holda navbatga qaytadi va admin boshqa qurilma tanlashi mumkin.
    """
    xabar.urinishlar = 0
    xabar.xato_matni = ""
    xabar.olingan = None
    if xabar.qurilma and xabar.qurilma.faol and xabar.qurilma.onlayn:
        xabar.holat = SmsXabar.Holat.BERILDI
        xabar.berilgan = timezone.now()
    else:
        xabar.holat = SmsXabar.Holat.NAVBATDA
        xabar.qurilma = None
        xabar.sim = None
        xabar.berilgan = None
    xabar.save(update_fields=["holat", "qurilma", "sim", "berilgan", "olingan",
                              "urinishlar", "xato_matni"])
    return xabar.holat


def hammasini_qayta_urin():
    xabarlar = SmsXabar.objects.filter(holat=SmsXabar.Holat.XATO).select_related("qurilma")
    soni = 0
    for xabar in xabarlar:
        qayta_urin(xabar)
        soni += 1
    return soni


# --------------------------------------------------------------------------
# Statistika
# --------------------------------------------------------------------------

def navbat_holati(davr=None):
    """Holatlar bo'yicha sanoq."""
    qs = SmsXabar.objects.all()
    if davr:
        qs = qs.filter(davr=oy_boshi(davr))
    sanoq = {kod: 0 for kod, _ in SmsXabar.Holat.choices}
    for qator in qs.values("holat").annotate(soni=Count("id")):
        sanoq[qator["holat"]] = qator["soni"]
    sanoq["jami"] = sum(sanoq.values())
    sanoq["kutmoqda"] = sanoq.get(SmsXabar.Holat.NAVBATDA, 0)
    sanoq["jarayonda"] = (sanoq.get(SmsXabar.Holat.BERILDI, 0)
                          + sanoq.get(SmsXabar.Holat.OLINDI, 0))
    return sanoq


def qurilmalar_holati():
    """Qurilmalar va ular bo'yicha qisqa sanoq."""
    qurilmalar = list(
        Qurilma.objects.prefetch_related("simlar").annotate(
            jonatgani=Count("xabarlar", filter=Q(xabarlar__holat=SmsXabar.Holat.JONATILDI)),
            jarayonda=Count("xabarlar", filter=Q(xabarlar__holat__in=[
                SmsXabar.Holat.BERILDI, SmsXabar.Holat.OLINDI])),
        )
    )
    onlayn = [q for q in qurilmalar if q.onlayn and q.faol]
    return {
        "royxat": qurilmalar,
        "jami": len(qurilmalar),
        "onlayn": len(onlayn),
        "onlayn_royxat": onlayn,
    }
