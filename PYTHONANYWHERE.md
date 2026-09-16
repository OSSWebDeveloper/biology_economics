# Saytni PythonAnywhere ga qo'yish

Bu qo'llanma saytni mijozning kompyuteridan **ochiq internetga** ko'chirish
uchun. Ko'chgandan keyin:

* sayt manzili — `https://mrclayd12.pythonanywhere.com`
* mijozning kompyuteri o'chiq bo'lsa ham sayt ishlaydi;
* telefondagi **Kurs SMS** ilovasi istalgan joydan (mobil internet bilan ham)
  ulanadi — Tailscale, oq IP, bir xil Wi-Fi kerak emas;
* oylik navbat o'zi tayyorlanadi (pastda, 11-bo'lim).

> **Ogohlantirish.** Ko'chib bo'lgandan keyin mijozning kompyuteridagi eski
> sayt **o'chirilishi shart**. Ikkalasi bir vaqtda ishlasa — ikkita alohida
> baza bo'lib qoladi va to'lovlar ikki joyda yuriladi.

---

## 0. Oldindan tayyor bo'lishi kerak

| Nima | Qayerdan |
|---|---|
| PythonAnywhere hisobi | https://www.pythonanywhere.com — foydalanuvchi: `MRClayd12` |
| Kod GitHub da | `https://github.com/OSSWebDeveloper/biology_economics` |
| Mijozning haqiqiy bazasi | Odilning kompyuteridagi `C:\bio_moliya\db.sqlite3` |

Bazani Odildan olib qo'ying — unda 9-sentabrdan beri kiritilgan haqiqiy
ma'lumot bor. Yangi bo'sh baza bilan boshlansa, hammasi yo'qoladi.

---

## 1. Kodni yuklab olish

PythonAnywhere da **Consoles → Bash** ni oching va:

```bash
git clone https://github.com/OSSWebDeveloper/biology_economics.git bio_moliya
cd bio_moliya
echo $HOME
```

Oxirgi buyruq uy papkangizni ko'rsatadi (masalan `/home/MRClayd12`). Quyida
`$UY` deb yozilgan joyga **o'sha yo'lni** qo'ying.

## 2. Virtual muhit va kutubxonalar

```bash
mkvirtualenv --python=/usr/bin/python3.13 bio_moliya
pip install -r requirements.txt
```

> Kompyuteringizda Python 3.14, PythonAnywhere da esa eng yangisi 3.13.
> Django 6.1 ikkalasida ham bir xil ishlaydi — muammo yo'q.

## 3. Sayt manzilini belgilash

```bash
cd ~/bio_moliya
echo "mrclayd12.pythonanywhere.com" > manzil.txt
```

Shu fayl borligi saytni **ochiq server rejimiga** o'tkazadi: `DEBUG` o'chadi,
faqat shu domen qabul qilinadi, cookie lar HTTPS ga bog'lanadi, parol
qoidalari kuchayadi. Fayl `.gitignore` da — GitHub ga tushmaydi, ya'ni
mahalliy nusxa eskisidek localhost da ishlayveradi.

## 4. Maxfiy kalit

```bash
python manage.py boshlangich
```

Serverga **yangi** maxfiy kalit yaratadi (mijoznikidan boshqa bo'lishi kerak).
Foydalanuvchi bo'lmasa `admin`/`admin` hisobini ham ochadi — parolni 8-bosqichda
albatta almashtiramiz.

## 5. Bazani yuklash

**Files** bo'limiga kiring → `bio_moliya` papkasiga o'ting → **Upload a file** →
Odilning `db.sqlite3` faylini yuklang (borini almashtiradi).

Keyin Bash da:

```bash
cd ~/bio_moliya
python manage.py migrate
python manage.py collectstatic --noinput
```

## 6. Veb-ilovani yaratish

**Web** bo'limi → **Add a new web app** →

1. Domen: `mrclayd12.pythonanywhere.com` → **Next**
2. **Manual configuration** (Django EMAS — biz o'zimiz sozlaymiz)
3. Python **3.13**

Keyin o'sha sahifada:

| Maydon | Qiymat |
|---|---|
| Source code | `$UY/bio_moliya` |
| Working directory | `$UY/bio_moliya` |
| Virtualenv | `$UY/.virtualenvs/bio_moliya` |

**Static files** jadvaliga bitta qator qo'shing:

| URL | Directory |
|---|---|
| `/static/` | `$UY/bio_moliya/staticfiles` |

## 7. WSGI fayli

Web bo'limidagi **WSGI configuration file** havolasini bosing
(`/var/www/mrclayd12_pythonanywhere_com_wsgi.py`). Ichidagi hamma narsani
o'chirib, o'rniga faqat shuni yozing (`$UY` ni o'z yo'lingizga almashtiring):

```python
import os
import sys

path = '/home/MRClayd12/bio_moliya'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Saqlang → Web bo'limiga qayting → **Reload** tugmasini bosing.

## 8. Xavfsizlik

**Web → Security** bo'limida **Force HTTPS** ni **Enabled** qiling → **Reload**.

Keyin saytga kiring: `https://mrclayd12.pythonanywhere.com`

**Parolni darhol almashtiring.** Eng yaxshisi — saytga `admin`/`admin` bilan
kirib, ichkaridan almashtirish. Ishlamasa, Bash da:

```bash
cd ~/bio_moliya
python manage.py sayt_admin --login admin --parol 'YANGI-KUCHLI-PAROL'
```

> Bu buyruq parolni konsol tarixida qoldiradi. Imkoni bo'lsa sayt orqali
> almashtiring.

Tekshirish:

```bash
python manage.py check --deploy
```

`no issues (2 silenced)` chiqishi kerak.

## 9. Telefondagi ilovani ulash

**Ilovani qayta qurish shart emas** — mavjud APK (v1.1.0) istalgan manzilga,
shu jumladan HTTPS ga ulanaveradi. Ikki yo'l bor.

### 9a. USB orqali (tavsiya) — bir bosishda

1. Saytga kiring → **Xabarnoma → Ulanish kodini olish** (12 xonalik kod,
   15 daqiqa amal qiladi).
2. Telefonni USB bilan ulang (telefonda **USB debugging** yoqilgan bo'lsin:
   Sozlamalar → Telefon haqida → "Build number" ni 7 marta bosing →
   Dasturchi sozlamalari → USB debugging).
3. Kompyuterda:

   ```
   QURILMA_QOSHISH.bat -Kod 049125081866
   ```

   Skript ilovani o'rnatadi, barcha ruxsatlarni beradi, batareya cheklovini
   olib tashlaydi, SMS chegarasini 200 ga oshiradi va manzil bilan kodni
   telefonga uzatadi. Telefon ekranida faqat **Ulanish** tugmasi bosiladi.

Manzil `qurilma_manzil.txt` da eslab qolingan. Boshqa saytga ulash kerak
bo'lsa: `QURILMA_QOSHISH.bat -Manzil https://boshqa.sayt -Kod 0491...`

Sayt ochiq internetda bo'lgani uchun skript **Tailscale qadamlarini
o'tkazib yuboradi** — shaxsiy tarmoq endi kerak emas.

### 9b. Qo'lda

Telefonda **Kurs SMS → Sozlamalar → Sayt manzili**:

```
https://mrclayd12.pythonanywhere.com
```

⚠️ **`https://` ni albatta yozing.** Yozilmasa ilova `http://` deb oladi,
server esa uni HTTPS ga buradi va ulanish xato beradi.

Keyin kodni kiriting → **Ulanish**. Ikkala tomonda "ulandi" bildirishnomasi
chiqadi. Telefondagi **Tailscale** endi kerak emas.

## 10. Sinov

`config/settings.py` dagi `SMS_TEST_RAQAM` ga o'z raqamingizni yozing, keyin:

```bash
python manage.py sms_eslatma --majburiy
```

Saytda **Xabarnoma → Xabarlar** → qurilma/SIM tanlang → **Yuborish**.
15 daqiqa ichida telefoningizga SMS kelishi kerak. Kelgach `SMS_TEST_RAQAM` ni
bo'shatib, saytni **Reload** qiling.

## 11. Oylik navbat qanday tayyorlanadi

Bepul tarifda rejalashtirilgan vazifa (Scheduled task) berilmaydi, lekin u
kerak emas:

* telefondagi ilova har 15 daqiqada `/sms/tekshir/` ga murojaat qiladi;
* shu murojaatda sayt "bugun navbat tayyorlanadigan kunmi?" deb tekshiradi;
* 1-sana bo'lsa — eslatmalar navbatga yoziladi, hech kim hech narsa bosmasa ham.

Navbat tayyorlanishi **SMS jo'natish degani emas**. SMS lar baribir admin
**Xabarlar → Yuborish** ni bosgandan keyin ketadi.

## 12. Doimiy ishlar

| Qachon | Nima |
|---|---|
| **Har oy** | Bepul veb-ilovaning muddati bir oy (API `expiry` maydonida ko'rinadi, masalan `2026-10-16`). Web bo'limiga kirib yangilash tugmasini bosing, aks holda sayt to'xtaydi. |
| **Har oy** | Files bo'limidan `db.sqlite3` ni yuklab olib, zaxiraga saqlang. Bepul tarifda avtomatik zaxira yo'q. |

## 13. Kodni yangilash

Kod o'zgarganda (GitHub ga push qilingandan keyin):

```bash
cd ~/bio_moliya
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Keyin **Web → Reload**.

`manzil.txt`, `maxfiy_kalit.txt` va `db.sqlite3` `.gitignore` da — `git pull`
ularga tegmaydi.

---

## Nima ishlamay qolishi mumkin

| Belgi | Sabab |
|---|---|
| `DisallowedHost` xatosi | `manzil.txt` dagi domen noto'g'ri yozilgan |
| Sayt bezaksiz, oq ekran | `collectstatic` qilinmagan yoki Static files yo'li xato |
| Ilova "ulanmadi" deydi | Manzil `https://` bilan yozilmagan (9-bosqich) |
| `ImportError: config` | WSGI faylidagi `path` noto'g'ri (`echo $HOME` bilan tekshiring) |
| Sayt butunlay ochilmaydi | oylik yangilash muddati o'tgan (12-bosqich) |

Xato sabablarini **Web → Log files → Error log** da ko'rish mumkin.
