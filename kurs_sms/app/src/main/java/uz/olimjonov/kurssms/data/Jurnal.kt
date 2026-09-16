package uz.olimjonov.kurssms.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Jurnal yozuvi. [turi]: "ok" | "xato" | "malumot" */
data class Yozuv(
    val vaqt: Long,
    val turi: String,
    val matn: String,
)

/**
 * Oxirgi harakatlar jurnali - bosh ekranda ko'rsatiladi.
 * Telefonning o'zida saqlanadi, hech qayerga yuborilmaydi.
 */
class Jurnal(context: Context) {

    private val p = context.applicationContext
        .getSharedPreferences("kurs_sms_jurnal", Context.MODE_PRIVATE)

    fun royxat(): List<Yozuv> {
        synchronized(qulf) {
            val xom = p.getString(KALIT, null)
            if (xom.isNullOrBlank()) return emptyList()
            return try {
                val massiv = JSONArray(xom)
                val natija = ArrayList<Yozuv>(massiv.length())
                for (i in 0 until massiv.length()) {
                    val obj = massiv.getJSONObject(i)
                    natija.add(
                        Yozuv(
                            vaqt = obj.optLong("v"),
                            turi = obj.optString("t", "malumot"),
                            matn = obj.optString("m", ""),
                        )
                    )
                }
                natija.asReversed()   // eng yangisi tepada
            } catch (e: Exception) {
                emptyList()
            }
        }
    }

    fun qosh(turi: String, matn: String) = synchronized(qulf) {
        val massiv = try {
            JSONArray(p.getString(KALIT, null) ?: "[]")
        } catch (e: Exception) {
            JSONArray()
        }
        massiv.put(
            JSONObject()
                .put("v", System.currentTimeMillis())
                .put("t", turi)
                .put("m", matn)
        )
        // faqat oxirgi ENG_KOP yozuv saqlanadi
        val qisqartirilgan = if (massiv.length() > ENG_KOP) {
            JSONArray().also { yangi ->
                for (i in (massiv.length() - ENG_KOP) until massiv.length()) {
                    yangi.put(massiv.get(i))
                }
            }
        } else {
            massiv
        }
        p.edit().putString(KALIT, qisqartirilgan.toString()).apply()
    }

    fun tozala() = synchronized(qulf) {
        p.edit().remove(KALIT).apply()
    }

    companion object {
        private const val KALIT = "yozuvlar"
        private const val ENG_KOP = 200
        private val qulf = Any()
    }
}
