# SMS moduli - "Xabarnoma" bo'limi

Har oyning **1-sanasida** qarzdor o'quvchilarning ota-onasiga kurs to'lovi
eslatmasi **navbatga** yoziladi. Sayt SMS jo'natmaydi: admin qaysi telefon va
qaysi SIM kartadan yuborishni tanlaydi, xabarlar o'sha qurilmalarga **teng**
bo'linadi, telefondagi **Kurs SMS** ilovasi esa ularni olib jo'natadi.

Ilova loyihasi shu repozitoriyda: `kurs_sms/` papkasi.

---

## 1. Ish tartibi

```
  SAYT (admin)                              TELEFON (Kurs SMS ilovasi)
  ────────────                              ──────────────────────────
  Xabarnoma -> "Ulanish kodini olish"
     12 xonalik kod (15 daqiqa)
                                   <───     POST /sms/ulan/   (kod + qurilma ma'lumoti)
     qurilma yaratiladi,           ───>     doimiy kalit
     "ulandi" bildirishnomasi                telefonda ham bildirishnoma chiqadi

  1-sanada navbat tayyorlanadi
     (qarzdorlar -> "navbatda")
  Xabarlar -> qurilma/SIM belgilash
     -> "Yuborish"
     xabarlar teng bo'linadi ("berildi")
                                   <───     GET  /sms/tekshir/  (har 15 daqiqada, "tirikman")
                                   <───     GET  /sms/navbat/   (o'ziga tegishlilari)
                                            SIM kartadan SMS jo'natadi
                                   <───     POST /sms/holat/    (jo'natildi / xato)
     "jo'natildi" yoki "Jo'natilmaganlar"
     bo'limida "Qayta urinib ko'rish"
```

### Xabarning holatlari

| Holat | Ma'nosi |
|---|---|
| `navbatda` | Tayyorlangan, lekin hali hech qaysi qurilmaga berilmagan |
| `berildi` | Admin yubordi, qurilma olishini kutmoqda |
| `olindi` | Ilova oldi, jo'natmoqda |
| `jonatildi` | Muvaffaqiyatli jo'natildi |
| `xato` | 3 marta urinildi, jo'natilmadi (qayta urinish mumkin) |

### Kafolatlar

* **Takror SMS ketmaydi.** Bazadagi cheklov: bir o'quvchiga, bir oyda, otaga
  bitta va onaga bitta xabar. Bundan tashqari ilova o'zi jo'natgan id larni
  eslab qoladi - natija saytga yetib bormay qolsa ham ikkinchi marta jo'natmaydi.
* **Xabar yo'qolmaydi.** Qurilma o'chib qolsa yoki internetdan uzilsa, unga
  berilgan xabarlar `SMS_BOSATISH_DAQIQA` (120 daqiqa) dan keyin navbatga
  qaytadi va boshqa qurilmaga berilishi mumkin.
* **Android chegarasi.** Bitta ilova 30 daqiqada 30 tadan ko'p SMS jo'natsa,
  tizim ekranda ruxsat so'raydi. Shuning uchun ilova bir tekshiruvda 10 ta
  xabar oladi (15 daqiqada 10 ta = 30 daqiqada 20 ta).

---

## 2. Sayt bo'limlari (faqat admin)

| Manzil | Nima bor |
|---|---|
| `/xabarnoma/` | Ulanish kodi, ulangan qurilmalar, onlayn holati, SIM lar, hodisalar |
| `/xabarnoma/xabarlar/` | Navbat, qurilma/SIM tanlash, "Yuborish", jarayondagilar |
| `/xabarnoma/xatolar/` | Jo'natilmagan xabarlar + "Qayta urinib ko'rish" |

Qurilma **onlayn** deb hisoblanadi, agar oxirgi 20 daqiqa ichida aloqa
bo'lgan bo'lsa (`Qurilma.ONLAYN_DAQIQA`).

Qurilmani **o'chirish** - vaqtincha ishlatmaslik (xabarlari navbatga qaytadi).
**Uzish** - butunlay o'chirish; qaytadan ulash uchun yangi kod kerak.

---

## 3. API (telefondagi ilova uchun)

Manzil asosi: `http(s)://<sayt>/sms/`

Ulanishdan tashqari har bir so'rovda qurilmaning kaliti bo'lishi shart:

```
X-SMS-Kalit: <kalit>
```

(`Authorization: Bearer <kalit>` ham qabul qilinadi.)

Kalit noto'g'ri yoki qurilma o'chirilgan → `403` (javobda `"qayta_ulaning": true`).
Modul o'chiq → `404`. Javoblar doim JSON.

### 3.1 `POST /sms/ulan/` - ulanish (kalitsiz)

```json
{
  "kod": "049125081866",
  "qurilma_id": "9f1c...-uuid",
  "nomi": "Samsung Galaxy A51",
  "ishlab_chiqaruvchi": "samsung",
  "model": "SM-A515F",
  "android": "13",
  "ilova_versiya": "1.0.0",
  "simlar": [
    {"id": 1, "nomi": "Beeline", "raqam": "901112233", "slot": 0},
    {"id": 2, "nomi": "Ucell", "raqam": "931112233", "slot": 1}
  ]
}
```

Javob: `{"ok": true, "kalit": "...", "sayt": "Biologiya kursi", "qurilma": "Samsung Galaxy A51", "simlar": 2}`

* `qurilma_id` - ilova o'rnatilganda bir marta yaratiladigan barqaror belgi.
  Xuddi shu belgi bilan qayta ulanilsa, yangi qurilma yaratilmaydi - eski
  yozuv yangilanadi va **kalit almashtiriladi**.
* Kod bir martalik va 15 daqiqa amal qiladi. Xato bo'lsa `400` va sabab:
  `{"ok": false, "xato": "Bu kod allaqachon ishlatilgan"}`

### 3.2 `GET /sms/tekshir/` - aloqa signali

Ixtiyoriy: `?batareya=77&versiya=1.0.0`

```json
{
  "ok": true,
  "sayt": "Biologiya kursi",
  "qurilma": "Samsung Galaxy A51",
  "vaqt": "2026-10-01T09:00:00+05:00",
  "navbatda": 4,
  "eng_yangi_versiya": "1.0.0"
}
```

Har chaqirilganda qurilmaning "oxirgi aloqa" vaqti yangilanadi - saytda
**onlayn** shu bilan ko'rinadi. `eng_yangi_versiya` - saytdagi
`SMS_ILOVA_VERSIYA`; ilova o'zinikidan kattaroq bo'lsa yangilanish haqida
ogohlantiradi.

### 3.3 `GET /sms/navbat/` - jo'natiladigan xabarlar

Ixtiyoriy: `?limit=10` (eng ko'pi 100).

```json
{
  "ok": true,
  "soni": 2,
  "xabarlar": [
    {"id": 41, "telefon": "+998901112233", "matn": "Assalomu alaykum! ...",
     "urinish": 1, "sim": 1},
    {"id": 42, "telefon": "+998901112244", "matn": "...", "urinish": 1, "sim": 2}
  ]
}
```

Faqat **shu qurilmaga berilgan** xabarlar qaytadi. `sim` - qaysi SIM dan
jo'natish kerakligi (ilovadagi `subscriptionId`); `-1` bo'lsa telefonning
standart SIM kartasi. Berilgan xabarlar darhol "olindi" deb belgilanadi va
30 daqiqa ichida javob kelmasa qayta beriladi (eng ko'pi 3 urinish).

### 3.4 `POST /sms/holat/` - natija

```json
{"natijalar": [
  {"id": 41, "holat": "jonatildi"},
  {"id": 42, "holat": "xato", "xato": "SIM kartada balans yo'q"}
]}
```

Javob: `{"ok": true, "qabul": 2}`

`holat` faqat `jonatildi` yoki `xato`. Xato bo'lsa urinishlar tugaguncha
qurilmada qoladi, tugagach saytdagi "Jo'natilmaganlar" bo'limiga tushadi.

### 3.5 `POST /sms/simlar/` - SIM ro'yxatini yangilash

```json
{"simlar": [{"id": 1, "nomi": "Beeline", "raqam": "901112233", "slot": 0}]}
```

SIM almashtirilganda ishlatiladi. Ro'yxatda yo'q SIM lar saytdan o'chiriladi.

---

## 4. Sozlamalar (`config/settings.py`)

| Sozlama | Ma'nosi |
|---|---|
| `SMS_ESLATMA_YOQILGAN` | asosiy kalit; `False` bo'lsa bo'lim menyudan ham, manzillardan ham yo'qoladi |
| `SMS_KIMGA` | `"ota"` / `"ona"` / `"ikkalasi"` |
| `SMS_MATN` | matn andozasi |
| `SMS_MATN_OTA`, `SMS_MATN_ONA` | otaga va onaga alohida matn (bo'sh bo'lsa umumiysi) |
| `SMS_YUBORISH_KUNI` | navbat oyning nechanchi sanasida tayyorlanadi (standart `1`) |
| `SMS_KECHIKISH_KUNI` | kompyuter o'chiq bo'lsa, necha kungacha kech tayyorlash mumkin |
| `SMS_ENG_KAM_QARZ` | shu summadan kichik qarzga xabar yozilmaydi |
| `SMS_URINISHLAR_CHEGARASI` | bitta xabarga necha marta urinib ko'rilsin |
| `SMS_BIR_MARTADA` | API bitta so'rovda eng ko'pi nechta xabar bersin |
| `SMS_BOSATISH_DAQIQA` | qurilmada qotib qolgan xabar qachon navbatga qaytariladi |
| `SMS_TEST_RAQAM` | bo'sh bo'lmasa - barcha xabarlar shu raqamga ketadi (sinov) |
| `SMS_ILOVA_VERSIYA` | telefondagi ilovaning eng yangi versiyasi |

Matn andozasidagi o'rinlar:
`{oquvchi}` `{ism}` `{familiya}` `{qarz}` `{kurs}` `{oy}` `{oldingi_oy}`

---

## 5. Buyruqlar

```
python manage.py sms_eslatma            # navbat tayyorlash (1-sanada)
python manage.py sms_eslatma --sinov    # bazaga yozmay, nima tayyorlanishini ko'rsatadi
python manage.py sms_eslatma --holat    # xabarlar va qurilmalar holati
python manage.py sms_eslatma --majburiy # 1-sanadan boshqa kunda ham tayyorlash
python manage.py sms_eslatma --sana 2026-11-01
```

Task Scheduler ga har oyning 1-sanasiga `python manage.py sms_eslatma`
qo'yiladi. Sayt bosh sahifasi ochilganda ham navbat o'zi tekshiriladi.

---

## 6. Birinchi marta sozlash

1. Telefonga ilovani o'rnating: `QURILMA_QOSHISH.bat` (manbasi `kurs_sms/`).
2. Ilovada sayt manzilini yozing.
3. Saytda **Xabarnoma → Ulanish kodini olish**.
4. Kodni ilovaga kiriting → **Ulanish**. Ikkala tomonda ham "ulandi"
   bildirishnomasi chiqadi.
5. `SMS_TEST_RAQAM` ga o'z raqamingizni yozib bir marta sinab ko'ring:
   `python manage.py sms_eslatma --majburiy` → Xabarlar → qurilma tanlash →
   Yuborish.
6. Hammasi joyida bo'lsa `SMS_TEST_RAQAM` ni bo'shating.

**Xavfsizlik.** Ilova saytga internet orqali ulanadi, ya'ni sayt tashqaridan
ochiq bo'lishi kerak. Manzil albatta **HTTPS** bo'lsin (kalit har so'rovda
yuboriladi). Kalit sizib chiqsa - o'sha qurilmani "Uzish" tugmasi bilan
o'chiring va qaytadan ulang.
