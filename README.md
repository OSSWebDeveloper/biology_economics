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
| 7/7 | Ish stoliga **ikkita yorliq** qo'yadi va dasturni ishga tushiradi |

> Oxirida savol berilmaydi. Avval "Ishga tushirilsinmi? [Y/N]" so'ralardi,
> lekin `choice` buyrug'i bosilgan tugmani emas, chiqqan **harfni** tekshiradi:
> klaviatura rus yoki o'zbek kirillchasida tursa `Y` tugmasi `Н` harfini beradi,
> buyruq uni rad etib faqat ovoz chiqaradi va oyna qotib qolgandek ko'rinadi.

Ish stolidagi ikkita yorliq:

| Yorliq | Vazifasi |
|---|---|
| **Dasturga kirish** | server fon rejimida (oynasiz) ishga tushadi va sayt **Chrome**'da ochiladi. Server allaqachon ishlayotgan bo'lsa — faqat Chrome ochiladi |
| **Serverni to'xtatish** | ishlab turgan serverni to'xtatadi va tasdiq oynasini ko'rsatadi |

### Soat yonidagi belgi (trey)

Server ishga tushganda soat yonida dastur belgisi paydo bo'ladi. **Belgi
turgan bo'lsa — server ishlayapti, yo'q bo'lsa — ishlamayapti.**

| Amal | Natija |
|---|---|
| **chap tugma** | saytni Chrome'da ochadi |
| **o'ng tugma** | "Dasturni yangilash" (ORNATISH.bat) va "Serverni to'xtatish" |

Belgi ustiga sichqoncha olib borilsa **"Biologiya kursi"** yozuvi chiqadi.

Belgi `Belgi.ps1` skripti — tashqi kutubxona kerak emas, Windows'ning o'z
.NET shakllari ishlatiladi. `Ishga_tushirish.vbs` uni ko'rinmas rejimda
chaqiradi; ikkinchi nusxa ochilmaydi (mutex). Har 3 sekundda port
tekshiriladi: server o'chsa belgi yo'qoladi, server 5 daqiqa ishlamasa
skript o'zini yopadi.

> Windows yangi trey belgilarini odatda **"^" strelkasi ostiga** yashiradi.
> Doim ko'rinib turishi uchun uni bir marta sichqoncha bilan panelga tortib
> chiqaring.

> Yorliqlar **foydalanuvchining o'z ish stoliga** qo'yiladi. Manzil UAC
> oynasidan OLDIN aniqlanadi: agar administrator huquqi boshqa hisob bilan
> berilsa, "ish stoli" o'sha hisobniki bo'lib qolar va yorliq ko'rinmay
> qolardi. OneDrive ish stolini o'ziga ko'chirgan kompyuterlarda ham shu
> manzil to'g'ri chiqadi.
>
> Ko'rinmasa: ish stolida bir marta **F5** bosing, bo'lmasa
> `C:io_moliya\Yorliqlarni_tiklash.bat` ni ishga tushiring — u qayerga
> qo'yayotganini ekranda ko'rsatadi. Windows Script Host o'chirilgan
> kompyuterda tayyor `.lnk` fayllari ko'chiriladi.

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

1. **ishlab turgan serverni to'xtatadi** — server `--noreload` bilan ishlaydi,
   ya'ni yangi fayllar faqat u qayta ishga tushgandan keyin kuchga kiradi;
2. GitHub'dan arxivni to'g'ridan-to'g'ri yuklab oladi (versiya alohida
   o'qilmaydi: GitHub fayllarni 5 daqiqagacha keshlaydi va push qilingan zahoti
   eski raqam kelib, yangilanish o'tkazib yuborilardi);
3. bazadan `db_zaxira_oxirgi.sqlite3` nusxasini olib, dastur fayllarini
   yangilaydi (robocopy o'zgarmagan fayllarni o'tkazib yuboradi) va `migrate`
   ni bajaradi;
4. **serverni yangi versiya bilan o'zi qayta ishga tushiradi** (agar u ish
   boshida ishlab turgan bo'lsa).

> Versiya raqami saytning chap pastki burchagida ko'rinadi. U ishga tushish
> paytida o'qiladi — demak eski raqam turgan bo'lsa, server qayta ishga
> tushmagan bo'ladi.

> **3.4.1 dan oldingi o'rnatuvchi** serverni to'xtatmasdi. Agar mijozda hali
> o'sha turgan bo'lsa (yoki biror sabab bilan server to'xtamasa), tartib
> shunday: ish stolidagi **"Serverni to'xtatish"** → keyin **ORNATISH.bat** →
> so'ng **"Dasturga kirish"**. Bir marta shunday yangilangandan keyin
> o'rnatuvchi buni o'zi bajaradigan bo'ladi.

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

Tizimda ikkita rol bor: **Admin** va **O'qituvchi**.

**Admin** — hamma narsani ko'radi va boshqaradi: barcha o'quvchilar, guruhlar,
xodimlar, oyliklar, moliyaviy hisobot. **Guruhni faqat admin yaratadi** va
guruhga o'qituvchini biriktiradi.

**O'qituvchi** — faqat **o'ziga biriktirilgan guruhlar** bilan ishlaydi:

| Ko'radi | Ko'rmaydi |
|---|---|
| o'z guruhlaridagi o'quvchilar | boshqa guruhlar va ularning o'quvchilari |
| o'z o'quvchilarining to'lovlari | xodimlar, oylik va avans |
| o'z guruhlari ro'yxati | moliyaviy hisobot (statistika) |
| Shaxsiy sahifam | guruh yaratish/tahrirlash |

O'qituvchi **o'z guruhiga o'quvchi qo'sha oladi**, ularni tahrirlaydi,
ro'yxatdan chiqaradi va **to'lov qabul qiladi**. Yangi o'quvchi formasida
guruh ro'yxatida faqat o'zining guruhlari chiqadi.

O'qituvchining bosh sahifasi ham boshqacha: u yerda guruhlari, o'quvchilari
soni va qarzdorlik holati ko'rinadi.

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

Kursxona boshlig'i xodimlar ro'yxatiga kiritilmaydi — u faqat `admin`
hisobiga ega bo'ladi. Xodimlar bo'limida faqat boshqa xodimlar ko'rinadi.

Texnik Django superuser hisobi bu tizimga umuman aralashmaydi.

## 4. Kurs to'lovi qanday hisoblanadi

Klient qoidasi:

1. **Kunlik narx = oylik kurs puli ÷ o'sha oydagi kunlar soni.**
   Sentabr 30 kun, oktabr 31 kun — kunlik narx har oyda boshqacha bo'ladi.
2. **Hisob oy tugagandan keyin yoziladi.** Yangi o'quvchi qo'shilganda uning
   qarzi **0** bo'ladi. Keyingi oyning **1-sanasida** o'tgan oyda qatnashgan
   kunlari hisoblanadi.
   *Misol:* oylik 200 000 so'm, o'quvchi 10-sentabrda keldi.
   Sentabrda 30 kun, kunlik 6 667 so'm. 1-oktabrda **21 kun** uchun
   **140 000 so'm** yoziladi.
3. **Har oyning 1-sanasida sikl qaytadan boshlanadi.** To'liq oy ishlagan
   o'quvchiga keyingi oyning 1-sanasida to'liq oylik summa yoziladi.
4. O'quvchi ro'yxatdan chiqarilsa, tugallanmagan oy **o'sha zahoti**
   qatnashgan kunlari bo'yicha hisoblanadi.
5. Hisoblar avtomatik ochiladi: sahifa ochilganda tizim yetishmayotgan
   oylarni o'zi hisoblab qo'yadi (takroriy yozuv chiqmaydi).

### Narx qayerdan olinadi

O'quvchi kartochkasidagi "Oylik kurs to'lovi" maydoni **ixtiyoriy**:

* bo'sh qoldirilsa — o'quvchi **guruh narxini** oladi va guruh narxi
  o'zgarsa avtomatik yangilanadi;
* narx yozilsa — aynan shu o'quvchi uchun o'sha narx ishlatiladi.

### Balans

| Balans | Ma'nosi | Rangi |
|---|---|---|
| manfiy | **qarzdor** | qizil |
| musbat | **oldindan to'langan** | yashil |
| nol | qarzi yo'q | kulrang |

O'quvchilar ro'yxatidagi **"To'lov"** tugmasi eng sodda oynachani ochadi:
naqd yoki plastik, va summa — boshqa hech narsa so'ralmaydi.

O'quvchi kartochkasidagi to'liq formada esa quyidagilar bor:

* **To'lov qabul qilish** — naqd yoki plastik;
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

### Guruhni o'zgartirish

O'quvchi kartochkasidagi **"Guruh"** kartochkasida **"Guruhni o'zgartirish"**
tugmasi bor. Oynachada yangi guruh tanlanadi (ro'yxatda har bir guruhning
oylik narxi ham ko'rinadi) va narx bilan nima bo'lishi belgilanadi:

* **Yangi guruh narxi qo'llansin** — o'quvchining shaxsiy narxi olib tashlanadi,
  endi guruh narxi amal qiladi;
* **Hozirgi narx saqlab qolinsin** — amaldagi narx o'quvchining o'ziga yoziladi,
  guruh narxi unga ta'sir qilmaydi.

To'lovlar, qarz va butun moliyaviy tarix saqlanib qoladi — faqat guruhi
almashadi. Narx o'zgarsa, shu oyning hisobiga ham ta'sir qiladi: oylik hisob
oy oxirida amaldagi narx bo'yicha yoziladi.

O'qituvchi faqat **o'z guruhlari** orasida ko'chira oladi, admin — hammasi.

### Arxivlash

O'quvchi kursni butunlay tugatganda **"Arxiv"** tugmasi bosiladi (ro'yxat
qatorida ham, kartochkada ham bor). Oynachada sabab tanlanadi:

| Sabab | Qo'shimcha maydon |
|---|---|
| **O'qishga kirdi** | biologiya bali va jami ball |
| **Sertifikat oldi** | sertifikat raqami/darajasi |
| **Guruhdan chetlatildi** | yo'q |

Saqlangach o'quvchi **guruhdan chiqariladi** (guruh ro'yxatlariga va
hisobotlariga aralashmaydi), ro'yxatdan olinadi va **Arxiv** bo'limiga o'tadi.
Moliyaviy tarixi to'liq saqlanadi; guruh olib tashlanishi bilan oylik narx
yo'qolmasligi uchun narx o'quvchining o'ziga ko'chiriladi va oxirgi
tugallanmagan oy qatnashgan kunlari bo'yicha yopiladi.

Arxiv bo'limi yorliqlarga bo'lingan: **Hammasi / O'qishga kirdi / Sertifikat
oldi / Guruhdan chetlatildi**. Xato arxivlangan bo'lsa — **"Arxivdan chiqarish"**;
o'quvchi "Chiqarilganlar" ro'yxatiga qaytadi, so'ng kartochkasidan ro'yxatga
qaytarilib guruh tayinlanadi.

---

## 6. Xodimlar oyligi va avans

* Oylik maoshni **faqat admin tayinlaydi** (xodim kartochkasi → "Oylik tayinlash").
* Har oyning 1-sanasida maosh avtomatik hisoblanadi. **Oylik kunlarga
  bo'linmaydi** — xodim ishga kirgan oyidan boshlab har oyga to'liq maosh
  yoziladi (o'quvchilardan farqli).
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
| **Ro'yxat → Qarzdorlar** | faqat qarzi bor o'quvchilar: jami qarz, eng katta qarz, oxirgi to'lov sanasi; chiqarilganlarni ham qo'shib ko'rsatish mumkin |
| **Guruhlar** | guruh nomi, dars jadvali, guruhning standart oylik to'lovi |
| **O'quvchi kartochkasi** | to'lov kiritish, hisob-kitob tarixi, guruhni o'zgartirish, arxivlash |
| **Arxiv** | kursni tugatganlar: o'qishga kirdi / sertifikat oldi / chetlatildi yorliqlari, ballari va oxirgi balansi |
| **Kurs to'lovlari** | barcha to'lovlar; amal turi, naqd/plastik, karta va sana bo'yicha filtr |
| **Xodimlar** | oylik maosh, shu oy avansi, qoldiq, saytga kirish logini |
| **Oylik va avans** | xodimlarga berilgan pullar; naqd/plastik alohida |
| **Moliya (statistika)** | kirim/chiqim, sof foyda, yig'ilish foizi, 12 oylik grafik, guruhlar kesimi |
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

# O'qituvchi hisobini qo'shish
python manage.py sayt_admin --login olim --parol "parol" --oqituvchi
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
│                  ranglar `app.css` ichidagi `:root` da - my.gov.uz
│                  palitrasi: ko'k #0079c1, och ko'k #4ab3e6, yashil #63ac5e
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
