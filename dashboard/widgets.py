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


class PulInput(forms.TextInput):
    """So'm summasi uchun maydon: 3000000 emas, 3 000 000 ko'rinishida.

    Raqamlar yozilayotganda uchtalab ajratiladi (app.js), yuborilganda esa
    bo'shliqlar shu yerda olib tashlanadi - shuning uchun JavaScript ishlamasa
    ham forma to'g'ri saqlanadi.
    """

    def __init__(self, attrs=None):
        birlashgan = {"inputmode": "numeric", "autocomplete": "off", "data-pul": "1"}
        if attrs:
            birlashgan.update(attrs)
        super().__init__(attrs=birlashgan)

    @staticmethod
    def _ajrat(matn):
        """1234567 -> '1 234 567'."""
        manfiy = matn.startswith("-")
        raqamlar = matn.lstrip("-")
        bolaklar = []
        while len(raqamlar) > 3:
            bolaklar.insert(0, raqamlar[-3:])
            raqamlar = raqamlar[:-3]
        bolaklar.insert(0, raqamlar)
        return ("-" if manfiy else "") + " ".join(bolaklar)

    def format_value(self, value):
        matn = super().format_value(value)
        if matn in (None, ""):
            return matn
        try:
            son = Decimal(str(matn).replace(" ", "").replace(",", "."))
        except (InvalidOperation, ValueError):
            return matn
        if son != son.to_integral_value():
            return matn
        return self._ajrat(str(son.quantize(Decimal("1"))))

    def value_from_datadict(self, data, files, name):
        qiymat = data.get(name)
        if isinstance(qiymat, str):
            return qiymat.replace(" ", "").replace(" ", "")
        return qiymat
