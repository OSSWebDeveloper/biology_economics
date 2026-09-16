"""Telefondagi ilova uchun API.

Manzillar `/sms/...` ostida. To'liq tavsif: `sms/API.md`.

Ulanish:
    POST /sms/ulan/       12 xonalik kod bilan - kalitsiz
Qolganlari kalit bilan:
    X-SMS-Kalit: <qurilmaning kaliti>      (Authorization: Bearer ham bo'ladi)

Modul o'chiq bo'lsa (`SMS_ESLATMA_YOQILGAN = False`) hammasi 404 qaytaradi.
"""
import json
from functools import wraps

from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import services, sozlamalar
from .models import Qurilma, SmsXabar


def _tana(request):
    """So'rov tanasini JSON sifatida o'qiydi."""
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return None


def _qurilma(request):
    kalit = (request.headers.get("X-SMS-Kalit") or "").strip()
    if not kalit:
        ruxsat = request.headers.get("Authorization", "")
        if ruxsat.lower().startswith("bearer "):
            kalit = ruxsat[7:].strip()
    if not kalit:
        return None
    return Qurilma.objects.filter(kalit=kalit, faol=True).first()


def ochiq_api(view):
    """Kalit talab qilmaydigan API (faqat ulanish)."""

    @csrf_exempt
    @login_not_required
    @wraps(view)
    def orab(request, *args, **kwargs):
        if not sozlamalar.yoqilgan():
            return JsonResponse({"ok": False, "xato": "topilmadi"}, status=404)
        return view(request, *args, **kwargs)

    return orab


def api(view):
    """Qurilma kaliti talab qilinadigan API."""

    @csrf_exempt
    @login_not_required
    @wraps(view)
    def orab(request, *args, **kwargs):
        if not sozlamalar.yoqilgan():
            return JsonResponse({"ok": False, "xato": "topilmadi"}, status=404)
        qurilma = _qurilma(request)
        if qurilma is None:
            return JsonResponse(
                {"ok": False, "xato": "kalit xato", "qayta_ulaning": True}, status=403
            )
        return view(request, qurilma, *args, **kwargs)

    return orab


# --------------------------------------------------------------------------

@ochiq_api
@require_POST
def ulan(request):
    """12 xonalik kod bilan qurilmani saytga ulaydi.

    Kutilayotgan tana:
        {"kod": "123456789012",
         "qurilma_id": "...", "nomi": "Samsung Galaxy A51",
         "ishlab_chiqaruvchi": "samsung", "model": "SM-A515F",
         "android": "13", "ilova_versiya": "1.0.0",
         "simlar": [{"id": 1, "nomi": "Beeline", "raqam": "+998...", "slot": 0}]}
    """
    malumot = _tana(request)
    if malumot is None:
        return JsonResponse({"ok": False, "xato": "JSON o'qilmadi"}, status=400)

    try:
        qurilma, kalit = services.qurilmani_ulash(malumot.get("kod"), malumot)
    except services.UlanishXatosi as xato:
        return JsonResponse({"ok": False, "xato": str(xato)}, status=400)

    return JsonResponse({
        "ok": True,
        "kalit": kalit,
        "sayt": sozlamalar.kurs_nomi(),
        "qurilma": qurilma.nomi,
        "simlar": qurilma.simlar.count(),
    })


@api
@require_GET
def tekshir(request, qurilma):
    """Aloqa signali va qisqa holat. Ilova buni davriy chaqiradi.

    Ilova har 15 daqiqada murojaat qilgani uchun oylik navbat ham shu yerda
    tekshiriladi - shunda hech kim saytni ochmasa ham 1-sanadagi eslatmalar
    o'zi tayyorlanadi va alohida rejalashtiruvchi (Task Scheduler / cron)
    kerak bo'lmaydi. Tayyorlash kuni bo'lmasa funksiya darhol qaytadi, ya'ni
    oddiy kunlarda qo'shimcha yuk yo'q.

    Bu faqat NAVBAT tayyorlaydi - SMS lar baribir admin "Yuborish" ni
    bosgandan keyin ketadi.
    """
    services.avtomatik_tekshir()
    services.aloqani_belgila(
        qurilma,
        batareya=request.GET.get("batareya"),
        ilova_versiya=request.GET.get("versiya", ""),
    )
    kutmoqda = SmsXabar.objects.filter(
        qurilma=qurilma,
        holat__in=[SmsXabar.Holat.BERILDI, SmsXabar.Holat.OLINDI],
    ).count()

    return JsonResponse({
        "ok": True,
        "sayt": sozlamalar.kurs_nomi(),
        "qurilma": qurilma.nomi,
        "vaqt": timezone.now().isoformat(),
        "navbatda": kutmoqda,
        "eng_yangi_versiya": sozlamalar.ilova_versiyasi(),
    })


@api
@require_POST
def simlar(request, qurilma):
    """Ilova SIM ro'yxatini yangilaydi (SIM almashtirilgan bo'lishi mumkin)."""
    malumot = _tana(request)
    if malumot is None:
        return JsonResponse({"ok": False, "xato": "JSON o'qilmadi"}, status=400)
    soni = services.simlarni_yangila(qurilma, malumot.get("simlar") or [])
    services.aloqani_belgila(qurilma)
    return JsonResponse({"ok": True, "soni": soni})


@api
@require_GET
def navbat(request, qurilma):
    """Shu qurilmaga berilgan xabarlarni beradi."""
    services.aloqani_belgila(qurilma)

    try:
        limit = int(request.GET.get("limit") or 0)
    except (TypeError, ValueError):
        limit = 0
    limit = min(limit, 100) if limit > 0 else None

    xabarlar = services.qurilma_navbati(qurilma, limit)
    return JsonResponse({
        "ok": True,
        "soni": len(xabarlar),
        "xabarlar": [{
            "id": x.pk,
            "telefon": x.telefon,
            "matn": x.matn,
            "urinish": x.urinishlar,
            "sim": x.sim.sim_id if x.sim_id else -1,
        } for x in xabarlar],
    })


@api
@require_POST
def holat(request, qurilma):
    """Ilova jo'natish natijasini qaytaradi.

        {"natijalar": [{"id": 12, "holat": "jonatildi"},
                       {"id": 13, "holat": "xato", "xato": "tarmoq yo'q"}]}
    """
    malumot = _tana(request)
    if malumot is None:
        return JsonResponse({"ok": False, "xato": "JSON o'qilmadi"}, status=400)

    natijalar = malumot.get("natijalar")
    if natijalar is None:
        natijalar = [malumot] if malumot.get("id") else []
    if not isinstance(natijalar, list):
        return JsonResponse({"ok": False, "xato": "natijalar ro'yxat bo'lishi kerak"},
                            status=400)

    services.aloqani_belgila(qurilma)

    qabul = 0
    for natija in natijalar[:200]:
        if not isinstance(natija, dict):
            continue
        kod = str(natija.get("holat") or "").strip().lower()
        if kod not in (SmsXabar.Holat.JONATILDI, SmsXabar.Holat.XATO):
            continue
        if services.holatni_belgila(natija.get("id"), kod, natija.get("xato", ""), qurilma):
            qabul += 1

    return JsonResponse({"ok": True, "qabul": qabul})
