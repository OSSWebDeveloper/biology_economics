# Kurs SMS

Android ilova. `bio_moliya` saytining **"Xabarnoma"** bo'limiga ulanadi,
o'ziga berilgan SMS xabarlarni internet orqali olib, telefonning SIM
kartasidan ota-onalarga jo'natadi.

Ilova shaxsiy - Play Market ga chiqarilmaydi, APK qo'lda o'rnatiladi.

---

## Nima qiladi

```
  SAYT (admin)                              TELEFON (shu ilova)
  ────────────                              ───────────────────
  Xabarnoma -> "Ulanish kodini olish"
     12 xonalik kod
                                   <───     kod bilan ulanadi, doimiy kalit oladi
  Xabarlar -> qurilma/SIM belgilash
     -> "Yuborish"
     xabarlar teng bo'linadi
                                   <───     har 15 daqiqada "tirikman" + navbat
                                            SIM kartadan SMS jo'natadi
                                   <───     natijani qaytaradi
     jo'natilmaganlar ro'yxati
     + "Qayta urinib ko'rish"
```

Bir nechta telefon ulanishi mumkin - sayt xabarlarni ular orasida teng
bo'ladi. Ikki SIM li telefonda har bir SIM alohida "kanal" bo'lib hisoblanadi.

Protokol: `D:\bio_moliya\sms\API.md`.

---

## Texnik tanlovlar

| Tanlov | Nima uchun |
|---|---|
| Kotlin + Jetpack Compose | XML layout yo'q, kod kamroq |
| WorkManager (doimiy xizmat emas) | Telefon qayta yoqilsa o'zi tiklanadi, doimiy bildirishnoma kerak emas, Android 14/15 ning foreground-service cheklovlariga tushmaydi |
| Ma'lumotlar bazasi yo'q | Sozlama va jurnal uchun SharedPreferences yetarli |
| `HttpURLConnection` + `org.json` | Retrofit/OkHttp/Gson kerak emas - beshta oddiy so'rov uchun ortiqcha |
| Har bir qurilmaga alohida kalit | Bitta telefonni saytdan uzib qo'yish mumkin, umumiy parol yo'q |
| Jo'natilgan id lar ro'yxati | Internet uzilsa ham bir xil SMS ikki marta ketmaydi |

### Takror SMS ketmasligi

Eng muhim joyi. SMS jo'natilgach natija saytga qaytariladi. Agar aynan shu
payt internet uzilsa, sayt xabarni 30 daqiqadan keyin qaytadan beradi.
Ilova esa jo'natgan xabar id larini o'zida saqlaydi (`Yuborilganlar`), shuning
uchun eski xabarni qaytadan jo'natmaydi - faqat natijasini qayta yuboradi.

### Android ning SMS chegarasi

Android bitta ilovaga **30 daqiqada 30 ta** dan ko'p SMS jo'natishga ruxsat
bermaydi - undan oshsa, ekranda "ruxsat berasizmi?" oynasi chiqadi va telefon
qarovsiz bo'lsa jo'natish to'xtab qoladi.

Shuning uchun ilova bir tekshiruvda **10 ta** xabar oladi (sozlamalardan
o'zgartiriladi). 15 daqiqada 10 ta = 30 daqiqada 20 ta - chegaradan past.
120 ta SMS taxminan 3 soatda jo'natiladi. Oylik eslatma uchun bu yetarli.
Ikkita telefon ulansa - ikki barobar tez.

---

## Loyiha tuzilishi

```
app/src/main/java/uz/olimjonov/kurssms/
├── MainActivity.kt              Ruxsatlar + ikkita ekran orasidagi harakat
├── KursSmsApp.kt                Bildirishnoma kanali
├── data/
│   ├── Prefs.kt                 Sozlamalar (manzil, kalit, qurilma belgisi...)
│   ├── Jurnal.kt                Oxirgi 200 ta harakat yozuvi
│   └── Yuborilganlar.kt         Jo'natilgan id lar - takrorlanishning oldini oladi
├── tarmoq/SaytApi.kt            /sms/ulan/, /tekshir/, /navbat/, /holat/, /simlar/
├── sms/
│   ├── SmsYuboruvchi.kt         SmsManager + natijani kutish (SIM tanlash bilan)
│   └── SimRoyxati.kt            Telefondagi SIM kartalar
├── ish/
│   ├── Ulanish.kt               12 xonalik kod bilan saytga ulanish
│   ├── SinxronMotor.kt          Bitta tekshiruv sikli (asosiy mantiq)
│   ├── SmsIsh.kt                WorkManager davriy ishi
│   ├── YoqishReceiver.kt        Telefon yoqilgach tiklash
│   └── Bildirishnoma.kt         "Saytga ulandi", "5 ta SMS jo'natildi"
└── ui/
    ├── AsosiyViewModel.kt
    ├── theme/Theme.kt
    └── ekran/
        ├── BoshEkran.kt         Holat, yoqish tugmasi, jurnal
        └── SozlamaEkran.kt      Manzil, ulanish kodi, SIM lar, tezlik
```

---

## Versiya

Versiya bitta joydan olinadi: loyiha ildizidagi **`versiya.txt`**
(saytdagi `bio_moliya\versiya.txt` bilan bir xil uslub).

```
1.0.0  ->  versionName = "1.0.0",  versionCode = 10000
```

`versionCode` avtomatik hisoblanadi: `katta*10000 + orta*100 + kichik`.

Versiya ikki joyda ko'rinadi:
* ilovaning Sozlamalar ekranida (pastda);
* saytdagi qurilmalar ro'yxatida ("ilova v1.0.0").

**Yangi versiya chiqarish:**
1. `versiya.txt` ni oshiring (masalan `1.1.0`).
2. `qur.bat assembleRelease`.
3. Saytdagi `SMS_ILOVA_VERSIYA` ni ham shu raqamga tenglang.
4. APK ni telefonga o'rnating (eskisining ustiga).

Saytdagi raqam ilovanikidan katta bo'lsa, ilova bosh ekranda
"yangi versiya bor" deb ogohlantiradi.

---

## Ruxsatlar

| Ruxsat | Nima uchun |
|---|---|
| `SEND_SMS` | Asosiy vazifa - SMS jo'natish |
| `INTERNET` | Sayt bilan aloqa |
| `POST_NOTIFICATIONS` | "Saytga ulandi", "5 ta SMS jo'natildi" (Android 13+) |
| `RECEIVE_BOOT_COMPLETED` | Telefon yoqilgach tekshiruvni tiklash |
| `READ_PHONE_STATE` | SIM ro'yxatini saytga ko'rsatish uchun (ixtiyoriy) |
| `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` | Tekshiruv kechikmasligi uchun |

Ilova hech qanday shaxsiy ma'lumotni hech qayerga yubormaydi: u faqat sizning
saytingizdan xabar olib, o'sha raqamlarga SMS jo'natadi.

---

## Qurish

Bu kompyuterda hamma narsa `D:\android` ga o'rnatilgan (Android Studio kerak emas):

```
D:\android\jdk          JDK 17
D:\android\sdk          Android SDK (platform-35, build-tools 35.0.0)
D:\android\gradle-8.9   Gradle
D:\android\gradle-home  Gradle keshi
```

```bat
cd /d D:\kurs_sms
qur.bat assembleRelease
```

Natija: `app\build\outputs\apk\release\app-release.apk`

Sinov uchun tezroq: `qur.bat assembleDebug`

### Imzo kaliti

`kurs_sms.jks` - release APK shu kalit bilan imzolanadi. Paroli
`kalit.properties` da. **Ikkalasi ham git ga tushmaydi.**

Kalitni yo'qotsangiz, keyingi versiyani telefonga yangilab o'rnata olmaysiz -
eskisini o'chirib, qaytadan o'rnatishga to'g'ri keladi. Shuning uchun
`kurs_sms.jks` faylini zaxiraga oling.

---

## Telefonga bir bosishda o'rnatish

**`TELEFONGA.bat`** — telefonni USB bilan ulab, shu faylni ikki marta bosing.
Skript o'zi hamma ishni qiladi:

| Qadam | Nima qiladi |
|---|---|
| 1 | `adb` ni topadi (avval `D:\android\sdk`, yo'q bo'lsa boshqa joylardan) |
| 2 | APK ni tekshiradi; yo'q bo'lsa **o'zi quradi** |
| 3 | Telefonni kutadi; topilmasa yoki ruxsat berilmasa — nima qilish kerakligini yozadi |
| 4 | APK ni o'rnatadi (`install -r -g`); eski imzo mos kelmasa — so'rab, eskisini o'chiradi |
| 5 | **Ruxsatlarni beradi**: SMS jo'natish, SIM ro'yxati, bildirishnomalar |
| 6 | Batareya tejash ro'yxatidan chiqaradi, "faol" guruhga qo'yadi, fonda ishlashga ruxsat beradi |
| 7 | Android ning SMS chegarasini (30 ta / 30 daqiqa) **200 ta** ga oshirishni taklif qiladi |
| 8 | Nima berilganini tekshirib ko'rsatadi |
| 9 | **Sayt manzili va 12 xonalik kodni so'rab, telefonga uzatadi** — ilova ochilib, tasdiq oynasini ko'rsatadi |

Ya'ni telefonda 12 raqamni qo'lda terish kerak emas: skript so'raydi, siz
saytdan nusxa olib qo'yasiz. Sayt manzili `sayt.txt` ga eslab qolinadi —
keyingi safar Enter bosish kifoya.

Telefonda faqat bitta **"Ulanish"** tugmasi bosiladi. Nega tasdiq kerak:
`MainActivity` boshqa ilovalar uchun ham ochiq (launcher ilovasi), shuning
uchun soxta manzil bilan ulab yuborishning oldi olinadi — oynada qaysi
saytga ulanayotganingiz yoziladi.

Kalitlar:

```
TELEFONGA.bat              oddiy - kerak joyda so'raydi
TELEFONGA.bat -Savolsiz    hech narsa so'ramaydi (hammasiga "ha")
TELEFONGA.bat -Qurmasin    APK yo'q bo'lsa qurmaydi, faqat xabar beradi

rem so'ramasdan, hammasini bir yo'la:
TELEFONGA.bat -Manzil "https://kurs.example.uz" -Kod 049125081866
```

**Telefonda oldindan kerak:** Sozlamalar → Telefon haqida → "Build number" ni
7 marta bosing → Dasturchi sozlamalari → **USB debugging = yoq**. Birinchi
ulanishda telefonda "ruxsat berilsinmi?" oynasi chiqadi — tasdiqlang
("bu kompyuterga doim ruxsat" ni belgilang).

### SMS chegarasi haqida

Android bitta ilovaga 30 daqiqada 30 tadan ko'p SMS jo'natishga ruxsat
bermaydi — undan oshsa ekranda oyna chiqadi va telefon qarovsiz bo'lsa
jo'natish to'xtab qoladi. Skript buni 200 ta ga oshiradi (7-qadam).
Qaytarish uchun:

```
D:\android\sdk\platform-tools\adb.exe shell settings put global sms_outgoing_check_max_count 30
```

---

## Qo'lda o'rnatish (USB kabelsiz)

1. `app-release.apk` ni telefonga ko'chiring (Telegram, Bluetooth).
2. Telefonda faylni oching → "Noma'lum manbadan o'rnatish" ga ruxsat bering.
3. Ilovani oching, SMS va bildirishnoma ruxsatlarini bering.
4. Sozlamalar (yuqori o'ngdagi tishli belgi) → **Sayt manzili** ni yozing.
5. Saytda: **Xabarnoma → Ulanish kodini olish**.
6. Chiqqan 12 raqamni ilovadagi **Ulanish kodi** maydoniga kiriting →
   **Ulanish**. Ikkala tomonda ham "ulandi" bildirishnomasi chiqadi.
7. Batareya ogohlantirishi chiqsa - "Ruxsat berish" ni bosing.

Ulangandan keyin avtomatik tekshirish o'zi yoqiladi.

### Sinash tartibi

1. Saytda `SMS_TEST_RAQAM` ga o'z raqamingizni yozing.
2. Saytda: `python manage.py sms_eslatma --majburiy`
3. Saytda: **Xabarlar** → qurilmani belgilang → **Yuborish**.
4. Ilovada **Hozir tekshirish** ni bosing - SMS o'z raqamingizga kelishi kerak.
5. Hammasi joyida bo'lsa `SMS_TEST_RAQAM` ni bo'shating.

---

## Nimalarga e'tibor berish kerak

* **Sayt internetdan ochiq bo'lishi shart.** Hozir sayt mijoz kompyuterida
  `localhost:8000` da ishlaydi - telefon unga faqat bir xil Wi-Fi da ulana
  oladi. Doimiy ishlashi uchun saytni tashqariga chiqarish kerak (tunnel
  orqali faqat `/sms/` manzilini ochish eng xavfsizi) va manzil **HTTPS**
  bo'lgani ma'qul, chunki kalit har so'rovda yuboriladi.
* **Telefonda SMS paketi bo'lsin.** Ilova operatorning tarifiga aralashmaydi.
* **Telefon doim yoqiq va internetda bo'lsin** - aks holda xabarlar navbatda
  kutib turadi (yo'qolmaydi) va 2 soatdan keyin boshqa qurilmaga o'tadi.
