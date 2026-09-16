package uz.olimjonov.kurssms.data

import android.content.Context

/**
 * Allaqachon jo'natilgan xabarlar ro'yxati (sayt bergan id lar).
 *
 * Nima uchun kerak: SMS jo'natilgach natijani saytga qaytarish paytida
 * internet uzilib qolsa, sayt o'sha xabarni 30 daqiqadan keyin qaytadan
 * beradi. Bu ro'yxat bo'lmasa, ota-onaga bir xil SMS ikki marta ketardi.
 * Endi esa ilova "bu allaqachon jo'natilgan" deb bilib, faqat natijasini
 * qaytadan yuboradi.
 */
class Yuborilganlar(context: Context) {

    private val p = context.applicationContext
        .getSharedPreferences("kurs_sms_yuborilgan", Context.MODE_PRIVATE)

    fun bormi(id: Long): Boolean = royxat().contains(id.toString())

    fun qosh(id: Long) {
        val royxat = royxat().toMutableList()
        if (royxat.contains(id.toString())) return
        royxat.add(id.toString())
        while (royxat.size > ENG_KOP) royxat.removeAt(0)
        p.edit().putString(KALIT, royxat.joinToString(",")).apply()
    }

    fun tozala() = p.edit().remove(KALIT).apply()

    private fun royxat(): List<String> {
        val xom = p.getString(KALIT, "") ?: ""
        return if (xom.isBlank()) emptyList() else xom.split(",")
    }

    companion object {
        private const val KALIT = "idlar"
        private const val ENG_KOP = 500
    }
}
