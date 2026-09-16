package uz.olimjonov.kurssms.data

import android.content.Context
import java.util.UUID

/** Ilova sozlamalari (telefonning o'zida saqlanadi). */
class Prefs(context: Context) {

    private val p = context.applicationContext
        .getSharedPreferences("kurs_sms", Context.MODE_PRIVATE)

    /** Sayt manzili, masalan: https://kurs.example.uz yoki http://192.168.1.5:8000 */
    var manzil: String
        get() = p.getString("manzil", "") ?: ""
        set(qiymat) = p.edit().putString("manzil", manzilniTogrila(qiymat)).apply()

    /**
     * Saytdan olingan doimiy kalit.
     *
     * Qo'lda kiritilmaydi: admin saytda 12 xonalik ulanish kodi chiqaradi,
     * ilova o'sha kod bilan ulanadi va saytning o'zi shu kalitni beradi.
     */
    var kalit: String
        get() = p.getString("kalit", "") ?: ""
        set(qiymat) = p.edit().putString("kalit", qiymat.trim()).apply()

    /** Saytdagi qurilma nomi (ulanish javobida keladi). */
    var qurilmaNomi: String
        get() = p.getString("qurilma_nomi", "") ?: ""
        set(qiymat) = p.edit().putString("qurilma_nomi", qiymat).apply()

    /** Sayt nomi (ulanish javobida keladi) - "qaysi saytga ulanganman". */
    var saytNomi: String
        get() = p.getString("sayt_nomi", "") ?: ""
        set(qiymat) = p.edit().putString("sayt_nomi", qiymat).apply()

    /**
     * Saytga oxirgi marta yuborilgan SIM ro'yxatining "imzosi".
     *
     * Har tekshiruvda hozirgi SIM lar bilan solishtiriladi: bir xil bo'lsa
     * ortiqcha so'rov yuborilmaydi, farq qilsa (SIM almashtirilgan, operator
     * nomi o'zgargan) sayt o'zi xabardor bo'ladi - tugma bosish shart emas.
     */
    var simlarImzosi: String
        get() = p.getString("simlar_imzosi", "") ?: ""
        set(qiymat) = p.edit().putString("simlar_imzosi", qiymat).apply()

    /**
     * Shu o'rnatishning barqaror belgisi.
     *
     * Ilova birinchi marta ochilganda yaratiladi va o'chirilmaguncha
     * o'zgarmaydi. Sayt shu belgi orqali "bu o'sha telefon" deb biladi:
     * qayta ulanganda yangi qurilma yaratmaydi.
     */
    val qurilmaId: String
        get() {
            val mavjud = p.getString("qurilma_id", "") ?: ""
            if (mavjud.isNotBlank()) return mavjud
            val yangi = UUID.randomUUID().toString()
            p.edit().putString("qurilma_id", yangi).apply()
            return yangi
        }

    /** Necha daqiqada bir tekshirilsin (Android eng kami 15 daqiqaga ruxsat beradi). */
    var oraliq: Int
        get() = p.getInt("oraliq", 15).coerceIn(15, 720)
        set(qiymat) = p.edit().putInt("oraliq", qiymat.coerceIn(15, 720)).apply()

    /** Ikki SMS orasidagi tanaffus (soniya) - operator spam deb hisoblamasligi uchun. */
    var tanaffus: Int
        get() = p.getInt("tanaffus", 4).coerceIn(0, 60)
        set(qiymat) = p.edit().putInt("tanaffus", qiymat.coerceIn(0, 60)).apply()

    /**
     * Bitta tekshiruvda eng ko'pi nechta SMS jo'natilsin.
     *
     * Android da ilova 30 daqiqada 30 tadan ko'p SMS jo'natsa, tizim
     * foydalanuvchidan "ruxsat berasizmi?" deb so'raydi va telefon
     * qarovsiz turgan bo'lsa jo'natish to'xtab qoladi. 15 daqiqada 10 ta
     * bo'lsa (30 daqiqada 20 ta) bu chegaraga yetmaydi.
     */
    var birMartada: Int
        get() = p.getInt("bir_martada", 10).coerceIn(1, 20)
        set(qiymat) = p.edit().putInt("bir_martada", qiymat.coerceIn(1, 20)).apply()

    /** Avtomatik tekshirish yoqilganmi. */
    var yoqilgan: Boolean
        get() = p.getBoolean("yoqilgan", false)
        set(qiymat) = p.edit().putBoolean("yoqilgan", qiymat).apply()

    /** Oxirgi tekshiruv vaqti (millisekund). */
    var oxirgiTekshiruv: Long
        get() = p.getLong("oxirgi", 0L)
        set(qiymat) = p.edit().putLong("oxirgi", qiymat).apply()

    /** Oxirgi tekshiruv natijasi (bosh ekranda ko'rsatiladi). */
    var oxirgiNatija: String
        get() = p.getString("natija", "") ?: ""
        set(qiymat) = p.edit().putString("natija", qiymat).apply()

    /** Saytdagi eng yangi ilova versiyasi (yangilanish haqida ogohlantirish uchun). */
    var engYangiVersiya: String
        get() = p.getString("eng_yangi", "") ?: ""
        set(qiymat) = p.edit().putString("eng_yangi", qiymat.trim()).apply()

    /** Sayt manzili bor va qurilma ulanganmi. */
    val ulangan: Boolean
        get() = manzil.isNotBlank() && kalit.isNotBlank()

    /** Ulanishni bekor qilish (kalit o'chiriladi, manzil qoladi). */
    fun ulanishniOchir() {
        p.edit()
            .remove("kalit")
            .remove("qurilma_nomi")
            .remove("sayt_nomi")
            .apply()
    }

    companion object {
        /** Foydalanuvchi kiritgan manzilni tartibga soladi. */
        fun manzilniTogrila(xom: String): String {
            var manzil = xom.trim().trimEnd('/')
            if (manzil.isEmpty()) return ""
            if (!manzil.startsWith("http://", true) && !manzil.startsWith("https://", true)) {
                manzil = "http://$manzil"
            }
            return manzil
        }

        /** "1.2.3" -> 10203; versiyalarni solishtirish uchun. */
        fun versiyaRaqami(versiya: String): Int {
            val bolaklar = versiya.split(".")
                .map { bolak -> bolak.filter(Char::isDigit).toIntOrNull() ?: 0 }
            val katta = bolaklar.getOrElse(0) { 0 }
            val orta = bolaklar.getOrElse(1) { 0 }
            val kichik = bolaklar.getOrElse(2) { 0 }
            return katta * 10000 + orta * 100 + kichik
        }
    }
}
