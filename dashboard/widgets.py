from decimal import Decimal, InvalidOperation

from django import forms


class SanaInput(forms.DateInput):
    """HTML5 sana tanlagichi.

    Brauzerning <input type="date"> maydoni faqat YYYY-MM-DD formatini tushunadi,
    o'zbek lokali esa standart holda 25.10.2006 ko'rinishida chiqaradi - shuning
    uchun format qat'iy belgilanadi, aks holda maydon bo'sh ko'rinadi.
    """

    input_type = "date"

    def __init__(self, attrs=None, format=None):
        birlashgan = {"type": "date"}
        if attrs:
            birlashgan.update(attrs)
        super().__init__(attrs=birlashgan, format=format or "%Y-%m-%d")


class PulInput(forms.NumberInput):
    """So'm summasi uchun maydon.

    So'mda tiyin ishlatilmaydi, shuning uchun 700000.00 emas, 700000 ko'rinishida
    chiqadi - aks holda brauzer uni "700000,00" qilib ko'rsatadi.
    """

    def __init__(self, attrs=None):
        birlashgan = {"step": "1000", "min": "0", "inputmode": "numeric"}
        if attrs:
            birlashgan.update(attrs)
        super().__init__(attrs=birlashgan)

    def format_value(self, value):
        matn = super().format_value(value)
        if matn in (None, ""):
            return matn
        try:
            son = Decimal(str(matn).replace(",", "."))
        except (InvalidOperation, ValueError):
            return matn
        if son == son.to_integral_value():
            return str(son.quantize(Decimal("1")))
        return matn
