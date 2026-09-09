# Biologiya kursi — moliyaviy boshqaruv tizimi

Biologiya kursi o'qituvchisi uchun o'quvchilar, kurs to'lovlari, qarzdorlik va
xodimlar oyligini yuritadigan veb-tizim. Python + Django, ma'lumotlar bazasi SQLite.
Tashqi kutubxonalar (bootstrap, chart.js va h.k.) ishlatilmaydi — internetsiz ham
to'liq ishlaydi.

Joriy versiya: [`versiya.txt`](versiya.txt)

---

## 1. Mijoz kompyuteriga o'rnatish — `ORNATISH.bat`

Bitta faylni **administrator nomidan** ishga tushirish kifoya
(o'ng tugma → *Run as administrator*):

```
ORNATISH.bat
```

U ketma-ket quyidagilarni bajaradi:

| Bosqich | Nima qiladi |
|---|---|
| 1/7 | Python 3.12+ borligini tekshiradi, bo'lmasa python.org dan yuklab o'rnatadi |
| 2/7 | GitHub'dagi versiya bilan kompyuterdagi versiyani solishtiradi |
| 3/7 | Yangilanish bo'lsa — dasturni GitHub'dan yuklab oladi |
| 4/7 | Fayllarni `C:\bio_moliya` ga ko'chiradi, **bazaga tegmaydi** |
| 5/7 | Virtual muhit ochib, Django va boshqa kutubxonalarni o'rnatadi |
| 6/7 | Bazani tayyorlaydi (`migrate`), birinchi marta bo'lsa admin hisobini ochadi |
| 7/7 | Ish stoliga **ikkita yorliq** qo'yadi |

Ish stolidagi ikkita yorliq:

| Yorliq | Vazifasi |
|---|---|
| **Dasturga kirish** | server fon rejimida (oynasiz) ishga tushadi va sayt **Chrome**'da ochiladi. Server allaqachon ishlayotgan bo'lsa — faqat Chrome ochiladi |
| **Serverni to'xtatish** | ishlab turgan serverni to'xtatadi va tasdiq oynasini ko'rsatadi |

### Sozlash

`ORNATISH.bat` ning boshidagi bir necha qatorni o'zgartirsangiz kifoya:

```bat
set "GITHUB=https://github.com/OSSWebDeveloper/biology_economics"
set "TARMOQ=main"
set "JOY=C:\bio_moliya"
set "PORT=8000"
```

> Internet bo'lmasa yoki manzil noto'g'ri bo'lsa, `ORNATISH.bat` o'zi turgan
> papkadagi nusxadan o'rnatadi — ya'ni butun papkani flashkada olib borib ham
> o'rnatsa bo'ladi.

### Papkadagi boshqa fayllar

| Fayl | Vazifasi |
|---|---|
| `Ishga_tushirish.vbs` | "Dasturga kirish" yorlig'i shuni chaqiradi |
| `Toxtatish.vbs` | "Serverni to'xtatish" yorlig'i shuni chaqiradi |
| `Server.bat` | Serverni ishga tushiradi, hammasini `server.log` ga yozadi |
| `Toxtatish.bat` | Fon rejimidagi serverni to'xtatadi |
| `Tekshirish.bat` | Serverni oynali rejimda ochadi — xatoni ko'rish uchun |
| `server.log` | Server jurnali; nimadir ishlamasa avval shuni oching |

---

## 2. Yangilash va versiyalar

Versiya raqami repozitoriyning ildizidagi `versiya.txt` faylida turadi.

**Yangi versiya chiqarish:**

1. Kodni o'zgartiring;
2. `versiya.txt` ichidagi raqamni oshiring (masalan `1.0.0` → `1.1.0`);
3. GitHub'ga push qiling.

**Mijoz tomonida:** `ORNATISH.bat` ni yana ishga tushirish kifoya. U:

* GitHub'dagi `versiya.txt` ni o'qiydi va kompyuterdagisi bilan solishtiradi;
* raqamlar bir xil bo'lsa — hech nima ko'chirmaydi, "oxirgi versiya turibdi" deydi;
* farq bo'lsa — bazadan `db_zaxira_oxirgi.sqlite3` nusxasini olib, dastur
  fayllarini yangilaydi va `migrate` ni bajaradi.

**Ma'lumotlar bazasi hech qachon almashtirilmaydi.** Yangilashda `db.sqlite3`,
`maxfiy_kalit.txt` va `port.txt` fayllariga tegilmaydi — o'quvchilar, to'lovlar,
xodimlar va parollar joyida qoladi.

---

## 3. Ikkita alohida kirish

| Panel | Manzil | Kimga |
|---|---|---|
| **Sayt paneli** (kundalik ish) | `/` | o'qituvchi, administrator |
| **Django admin** (texnik) | `/boshqaruv/` | dasturchi |

Bu ikkalasi **bir-biridan butunlay mustaqil**: sayt admini `/boshqaruv/` ga kira
olmaydi, Django superuseri esa sayt paneliga kira olmaydi
(`saytga_kira_oladi` bayrog'i o'chirilgan). Parollari ham boshqa-boshqa.

Dastur **o'z admini bilan keladi** - birinchi o'rnatishda avtomatik ochiladi:

```
login: admin
parol: admin
```

> Saytga birinchi kirgandan keyin **"Shaxsiy sahifam"** bo'limidan parolni
> albatta almashtiring.

Buyruq orqali ham almashtirsa bo'ladi:

```bash
python manage.py sayt_admin --login admin --parol "YANGI_PAROL"
```

Django admin uchun texnik hisob alohida yaratiladi:

```bash
python manage.py createsuperuser
```

### Rollar

* **Sayt admini** — hamma narsa: xodim oyligini tayinlash, yozuvni o'chirish,
  guruh va karta boshqarish, foydalanuvchilarni boshqarish.
* **Operator** — o'quvchi qo'shish/tahrirlash, to'lov qabul qilish, ro'yxatdan
  chiqarish, hisobotlarni ko'rish. Oylik tayinlash va o'chirish huquqi yo'q.

### Shaxsiy sahifam

Yon menyudagi **Sozlamalar —> Shaxsiy sahifam** bo'limida har bir foydalanuvchi
(boshliq ham, o'qituvchi ham) **faqat o'zi haqidagi** ma'lumotni boshqaradi:

* familiya, ism, telefon va **login**;
* **parol** — joriy parolni so'raydi, almashtirgandan keyin saytdan chiqib ketmaydi.

Ismini o'zgartirsa, xodim kartochkasidagi ismi ham avtomatik yangilanadi.

### Xodimlarga login berish

Bu **yopiq tizim** — hech kim o'zi ro'yxatdan o'ta olmaydi. O'qituvchining
saytga kirish logini uning **xodim kartochkasidan** beriladi:

**Xodimlar —> xodimni ochish —> "Saytga kirish"** paneli (faqat admin ko'radi):

* login va parol yozib **"Login yaratish"** — xodimga hisob ochiladi, ismi
  kartochkadan olinadi;
* keyinchalik shu paneldan **login, parol va huquqni** o'zgartirish mumkin
  (parol bo'sh qoldirilsa, eskisi o'zgarmaydi);
* **"Kirish huquqini olib tashlash"** — xodim saytga kira olmaydigan bo'ladi,
  lekin oylik va to'lovlar tarixi joyida qoladi;
* xodimning logini allaqachon bo'lsa, **"Mavjud hisobni bog'lash"** orqali
  ulanadi.

Xodimlar ro'yxatida "Login" ustuni kimda kirish borligini ko'rsatib turadi.
Har bir xodimga login shart emas — oylik va to'lovlar loginsiz ham yuritiladi.

Birinchi o'rnatishda kursxona boshlig'i uchun **`admin` hisobi ham, xodim
kartochkasi ham** birga ochiladi (u ham boshliq, ham o'qituvchi).

Texnik Django superuser hisobi bu tizimga umuman aralashmaydi.

## 4. Kurs to'lovi qanday hisoblanadi

Klient aytgan qoida to'liq shunday amalga oshirilgan:

1. **Kunlik narx = oylik kurs puli ÷ o'sha oydagi kunlar soni.**
   Sentabr 30 kun, oktabr 31 kun — kunlik narx har oyda boshqacha bo'ladi.
2. **O'quvchi oy o'rtasida kelsa**, kelgan kunidan keyingi oyning 1-sanasigacha
   bo'lgan kunlar uchun to'laydi.
   *Misol:* oylik 600 000 so'm, sentabrda 30 kun → kunlik 20 000 so'm.
   15-sentabrda kelgan o'quvchi 15–30 sentabr = **16 kun × 20 000 = 320 000 so'm**.
3. **1-sanadan yangi sikl** boshlanadi — to'liq oylik summa yoziladi.
4. Hisoblar avtomatik ochiladi: sahifa ochilganda tizim yetishmayotgan oylarni
   o'zi hisoblab qo'yadi (takroriy yozuv chiqmaydi).

### Balans

| Balans | Ma'nosi | Rangi |
|---|---|---|
| manfiy | **qarzdor** | qizil |
| musbat | **oldindan to'langan** | yashil |
| nol | qarzi yo'q | kulrang |

Kiritish mumkin bo'lgan amallar (o'quvchi oynachasida):

* **To'lov qabul qilish** — naqd yoki plastik (karta raqami bilan);
* **Chegirma berish** — qarzni kamaytiradi;
* **O'qituvchi qarzi** — dars o'tkazilmasa yoki o'qituvchi o'quvchidan qarz
  bo'lib qolsa, summa **oldindan to'langan pul hisobiga** o'tadi (klient talabi);
* **Pulni qaytarib berish** — kassadan chiqim.

Avtomatik "Hisoblangan kurs to'lovi" yozuvini qo'lda o'chirib bo'lmaydi —
u faqat o'quvchi ro'yxatdan chiqarilganda qayta hisoblanadi.

---

## 5. Ro'yxatdan chiqarish

O'quvchi kartochkasida **"Ro'yxatdan chiqarish"** tugmasi:

* o'quvchi kursga keladiganlar ro'yxatidan olinadi, lekin **moliyaviy tarixi saqlanadi**;
* chiqarilgan sanadan keyingi oylarga pul yozilmaydi;
* "oxirgi oyni kunlarga bo'lib qayta hisoblansin" belgisi qo'yilsa, oxirgi oy
  faqat qatnashgan kunlari uchun qayta hisoblanadi;
* keyin qaytsa — **"Ro'yxatga qaytarish"**, yangi kelgan sanasi so'raladi va
  o'sha sanadan yangi hisob boshlanadi.

Butunlay o'chirish (tarixi bilan) faqat adminda va alohida tasdiqlash bilan.

---

## 6. Xodimlar oyligi va avans

* Oylik maoshni **faqat admin tayinlaydi** (xodim kartochkasi → "Oylik tayinlash").
* Har oyning 1-sanasida maosh avtomatik hisoblanadi; xodim oy o'rtasida ishga
  kirsa — o'quvchilardagi kabi kunlab bo'linadi.
* **Avans** va **oylik** alohida yoziladi, ikkalasi ham naqd yoki plastik bo'lishi
  mumkin. "Oylik va avans" bo'limida naqd/plastik bo'yicha filtr bor.
* **Qoldiq**: musbat — xodimga to'lanishi kerak; manfiy — ortiqcha avans berilgan.
* Bonus/ustama qo'shish va ushlab qolish (jarima) ham bor.

---

## 7. Bo'limlar

| Bo'lim | Nima qiladi |
|---|---|
| **Bosh sahifa** | tezkor amallar, bugungi va oylik tushum, qarzdorlar, oxirgi to'lovlar |
| **O'quvchilar → Ro'yxat** | qidiruv, guruh/to'lov holati bo'yicha filtr; qatorga bosilsa to'lov oynachasi ochiladi |
| **Guruhlar** | guruh nomi, dars jadvali, guruhning standart oylik to'lovi |
| **Kurs to'lovlari** | barcha to'lovlar; amal turi, naqd/plastik, karta va sana bo'yicha filtr |
| **Xodimlar** | oylik maosh, shu oy avansi, qoldiq, saytga kirish logini |
| **Oylik va avans** | xodimlarga berilgan pullar; naqd/plastik alohida |
| **Moliya (statistika)** | kirim/chiqim, sof foyda, yig'ilish foizi, 12 oylik grafik, guruh va karta kesimi |
| **Kartalar** | to'lov qabul qilinadigan plastik kartalar ro'yxati |
| **Shaxsiy sahifam** | o'z familiyasi, ismi, logini va parolini o'zgartirish |

---

## 8. Dasturchi uchun

```bash
# Ishga tushirish
python manage.py runserver

# Testlar
python manage.py test

# Yetishmayotgan oylik hisoblarni ochish (zaxira; sayt o'zi ham qiladi)
python manage.py hisoblash

# Birinchi ishga tushirish tayyorgarligi - kalit + admin hisobi
python manage.py boshlangich

# Sayt admini yaratish / parolini yangilash
python manage.py sayt_admin --login admin --parol "yangi_parol"

# Operator qo'shish
python manage.py sayt_admin --login operator1 --parol "parol" --operator
```

### Namunaviy ma'lumot

```bash
python manage.py namuna            # 18 o'quvchi, 3 guruh, 3 xodim qo'shadi
python manage.py namuna --tozala   # barcha o'quvchi/xodim/to'lovni o'chiradi
```

> `--tozala` ni haqiqiy ish boshlangandan keyin **ishlatmang**.

### Loyiha tuzilishi

```
bio_moliya/
├─ config/          sozlamalar va manzillar
├─ accounts/        sayt foydalanuvchilari, kirish, Django admin ajratmasi
├─ students/        guruhlar va o'quvchilar
├─ payments/        kurs to'lovlari + hisoblash mantiqi (services.py)
├─ staff/           xodimlar, oylik va avans
├─ dashboard/       bosh sahifa va moliya statistikasi
├─ templates/       sahifalar
├─ static/          css va js (tashqi kutubxonasiz)
├─ versiya.txt      dastur versiyasi - yangilash shunga qarab ishlaydi
└─ ORNATISH.bat     mijoz kompyuteriga o'rnatuvchi
```

Asosiy hisoblash mantiqi ikki faylda:
`payments/services.py` (kurs to'lovi) va `staff/services.py` (oylik).

---

## 9. Zaxira nusxa (backup)

Butun baza bitta faylda: `db.sqlite3`. Uni vaqti-vaqti bilan flashka yoki
Google Drive'ga ko'chirib turing:

```bash
copy C:\bio_moliya\db.sqlite3 D:\zaxira\db_2026-09-09.sqlite3
```

`ORNATISH.bat` yangilashdan oldin ham avtomatik nusxa oladi:
`C:\bio_moliya\db_zaxira_oxirgi.sqlite3`.

---

## 10. Aniqlanishi kerak bo'lgan savollar

Quyidagilar mantiqiy standart bilan qilingan, klient boshqacha desa oson o'zgaradi:

1. **Chiqarilgan kun to'lanadimi?** Hozir chiqarilgan sana ham to'lanadigan kun
   sifatida hisoblanadi (masalan 10-sanada chiqsa, 1–10 = 10 kun).
2. **Guruhlar** klient aytmagan, lekin qo'shildi — filtr va hisobot uchun qulay.
   Kerak bo'lmasa, o'quvchini guruhsiz qoldirsa bo'ladi.
3. **Karta raqami** — to'lov *qabul qilingan* karta (o'qituvchining kartasi)
   sifatida tushunildi; kartalar ro'yxatdan tanlanadi.
4. **Dars qoldirish (davomat)** hisoblanmaydi — to'lov kalendar kunlari bo'yicha,
   klient aytganidek.

---

## 11. Xavfsizlik eslatmasi

Parol qoidalari ataylab yengil qoldirilgan (kamida 4 ta belgi) - shuning uchun
standart `admin` / `admin` juftligi ishlaydi. Sayt faqat shu kompyuterda
ochilgani uchun bu xavfli emas, lekin baribir birinchi kirishdan keyin parolni
almashtirish tavsiya etiladi.

Sayt faqat `127.0.0.1` (shu kompyuter) uchun ochiladi — tarmoqdan kirib bo'lmaydi.
Boshqa kompyuterlardan ham kirish kerak bo'lsa, `Server.bat` dagi manzilni
`0.0.0.0:%PORT%` ga o'zgartiring va `config/settings.py` da `ALLOWED_HOSTS`
ni to'ldiring. Bunday holatda `DEBUG = False` qilish ham tavsiya etiladi.
