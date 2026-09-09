"""Shablonlar uchun pul va sana yordamchilari."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def som(qiymat):
    """12500000 -> "12 500 000" ko'rinishida chiqaradi."""
    if qiymat is None or qiymat == "":
        return "0"
    try:
        son = Decimal(qiymat)
    except (InvalidOperation, TypeError, ValueError):
        return qiymat
    manfiy = son < 0
    son = abs(son).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    matn = f"{son:,}".replace(",", " ")
    return f"-{matn}" if manfiy else matn


@register.filter
def musbat(qiymat):
    """Manfiy sonni musbat qilib qaytaradi (qarz summasini ko'rsatish uchun)."""
    try:
        return abs(Decimal(qiymat))
    except (InvalidOperation, TypeError, ValueError):
        return qiymat


@register.filter
def balans_klass(qiymat):
    try:
        son = Decimal(qiymat)
    except (InvalidOperation, TypeError, ValueError):
        return ""
    if son < 0:
        return "qarz"
    if son > 0:
        return "oldindan"
    return "toza"


@register.simple_tag(takes_context=True)
def sorov_bilan(context, **kwargs):
    """Joriy GET parametrlarini saqlab, ba'zilarini almashtiradi."""
    sorov = context["request"].GET.copy()
    for kalit, qiymat in kwargs.items():
        if qiymat in (None, ""):
            sorov.pop(kalit, None)
        else:
            sorov[kalit] = qiymat
    if "sahifa" not in kwargs:
        sorov.pop("sahifa", None)
    return sorov.urlencode()
