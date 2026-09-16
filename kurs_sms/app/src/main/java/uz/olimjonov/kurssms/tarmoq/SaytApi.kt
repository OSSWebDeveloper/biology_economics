package uz.olimjonov.kurssms.tarmoq

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import uz.olimjonov.kurssms.sms.Sim
import java.io.IOException
import java.net.ConnectException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.UnknownHostException
import javax.net.ssl.SSLException

/** Saytdan kelgan bitta xabar. [sim] = -1 bo'lsa standart SIM ishlatiladi. */
data class Xabar(
    val id: Long,
    val telefon: String,
    val matn: String,
    val urinish: Int,
    val sim: Int = -1,
)

/** Saytning qisqa holati (`/sms/tekshir/`). */
data class SaytHolat(
    val sayt: String,
    val qurilma: String,
    val navbatda: Int,
    val engYangiVersiya: String,
    /**
     * Sayt hozir qurilmalarni qabul qilmayapti (admin "qabul oynasi" ni
     * ochmagan yoki muddati o'tgan). Bu XATO EMAS - shunchaki hozircha ish
     * yo'q degani, shuning uchun sayt buni 200 bilan qaytaradi.
     */
    val yopiq: Boolean = false,
)

/** Ulanish natijasi (`/sms/ulan/`). */
data class Ulanish(
    val kalit: String,
    val sayt: String,
    val qurilma: String,
    val simlar: Int,
)

/** Qurilma haqida saytga yuboriladigan ma'lumot. */
data class QurilmaMalumoti(
    val qurilmaId: String,
    val nomi: String,
    val ishlabChiqaruvchi: String,
    val model: String,
    val android: String,
    val ilovaVersiya: String,
    val simlar: List<Sim>,
)

/** Bitta xabarning jo'natish natijasi. */
data class YuborishNatijasi(
    val id: Long,
    val jonatildi: Boolean,
    val xato: String = "",
)

sealed interface Javob<out T> {
    data class Ok<T>(val qiymat: T) : Javob<T>
    data class Xato(val kod: Int, val xabar: String) : Javob<Nothing>
}

/**
 * Sayt bilan aloqa. Protokol: `sms/API.md` (bio_moliya loyihasi).
 *
 * Ulanishdan tashqari har bir so'rovda `X-SMS-Kalit` sarlavhasi yuboriladi.
 */
class SaytApi(manzil: String, private val kalit: String = "") {

    private val asos = manzil.trimEnd('/')

    /** 12 xonalik kod bilan saytga ulanish. Kalit talab qilinmaydi. */
    suspend fun ulan(kod: String, malumot: QurilmaMalumoti): Javob<Ulanish> =
        withContext(Dispatchers.IO) {
            val simlar = JSONArray()
            for (sim in malumot.simlar) {
                simlar.put(
                    JSONObject()
                        .put("id", sim.id)
                        .put("nomi", sim.nomi)
                        .put("raqam", sim.raqam)
                        .put("slot", sim.slot)
                )
            }
            val tana = JSONObject()
                .put("kod", kod.filter(Char::isDigit))
                .put("qurilma_id", malumot.qurilmaId)
                .put("nomi", malumot.nomi)
                .put("ishlab_chiqaruvchi", malumot.ishlabChiqaruvchi)
                .put("model", malumot.model)
                .put("android", malumot.android)
                .put("ilova_versiya", malumot.ilovaVersiya)
                .put("simlar", simlar)
                .toString()

            when (val javob = sorov("/sms/ulan/", "POST", tana, kalitsiz = true)) {
                is Javob.Xato -> javob
                is Javob.Ok -> try {
                    val obj = JSONObject(javob.qiymat)
                    Javob.Ok(
                        Ulanish(
                            kalit = obj.optString("kalit", ""),
                            sayt = obj.optString("sayt", ""),
                            qurilma = obj.optString("qurilma", ""),
                            simlar = obj.optInt("simlar", 0),
                        )
                    )
                } catch (e: Exception) {
                    Javob.Xato(0, "Javob tushunarsiz - manzil to'g'rimi?")
                }
            }
        }

    suspend fun tekshir(batareya: Int = -1, versiya: String = ""): Javob<SaytHolat> =
        withContext(Dispatchers.IO) {
            val savol = buildString {
                append("/sms/tekshir/")
                val qismlar = mutableListOf<String>()
                if (batareya in 0..100) qismlar.add("batareya=$batareya")
                if (versiya.isNotBlank()) qismlar.add("versiya=$versiya")
                if (qismlar.isNotEmpty()) append("?").append(qismlar.joinToString("&"))
            }
            when (val javob = sorov(savol, "GET", null)) {
                is Javob.Xato -> javob
                is Javob.Ok -> try {
                    val obj = JSONObject(javob.qiymat)
                    Javob.Ok(
                        SaytHolat(
                            sayt = obj.optString("sayt", ""),
                            qurilma = obj.optString("qurilma", ""),
                            navbatda = obj.optInt("navbatda", 0),
                            engYangiVersiya = obj.optString("eng_yangi_versiya", ""),
                            yopiq = obj.optBoolean("yopiq", false),
                        )
                    )
                } catch (e: Exception) {
                    Javob.Xato(0, "Javob tushunarsiz - bu sayt manzili to'g'rimi?")
                }
            }
        }

    /** SIM ro'yxatini saytga yuboradi (SIM almashtirilgan bo'lishi mumkin). */
    suspend fun simlarniYubor(simlar: List<Sim>): Javob<Int> = withContext(Dispatchers.IO) {
        val massiv = JSONArray()
        for (sim in simlar) {
            massiv.put(
                JSONObject()
                    .put("id", sim.id)
                    .put("nomi", sim.nomi)
                    .put("raqam", sim.raqam)
                    .put("slot", sim.slot)
            )
        }
        val tana = JSONObject().put("simlar", massiv).toString()
        when (val javob = sorov("/sms/simlar/", "POST", tana)) {
            is Javob.Xato -> javob
            is Javob.Ok -> Javob.Ok(
                try {
                    JSONObject(javob.qiymat).optInt("soni", 0)
                } catch (e: Exception) {
                    0
                }
            )
        }
    }

    suspend fun navbat(limit: Int = 10): Javob<List<Xabar>> = withContext(Dispatchers.IO) {
        when (val javob = sorov("/sms/navbat/?limit=$limit", "GET", null)) {
            is Javob.Xato -> javob
            is Javob.Ok -> try {
                val massiv = JSONObject(javob.qiymat).optJSONArray("xabarlar") ?: JSONArray()
                val royxat = ArrayList<Xabar>(massiv.length())
                for (i in 0 until massiv.length()) {
                    val obj = massiv.getJSONObject(i)
                    val telefon = obj.optString("telefon", "")
                    val matn = obj.optString("matn", "")
                    if (telefon.isBlank() || matn.isBlank()) continue
                    royxat.add(
                        Xabar(
                            id = obj.optLong("id"),
                            telefon = telefon,
                            matn = matn,
                            urinish = obj.optInt("urinish", 0),
                            sim = obj.optInt("sim", -1),
                        )
                    )
                }
                Javob.Ok(royxat)
            } catch (e: Exception) {
                Javob.Xato(0, "Navbat o'qilmadi")
            }
        }
    }

    suspend fun holat(natijalar: List<YuborishNatijasi>): Javob<Int> =
        withContext(Dispatchers.IO) {
            if (natijalar.isEmpty()) return@withContext Javob.Ok(0)
            val massiv = JSONArray()
            for (natija in natijalar) {
                massiv.put(
                    JSONObject()
                        .put("id", natija.id)
                        .put("holat", if (natija.jonatildi) "jonatildi" else "xato")
                        .put("xato", natija.xato)
                )
            }
            val tana = JSONObject().put("natijalar", massiv).toString()
            when (val javob = sorov("/sms/holat/", "POST", tana)) {
                is Javob.Xato -> javob
                is Javob.Ok -> Javob.Ok(
                    try {
                        JSONObject(javob.qiymat).optInt("qabul", 0)
                    } catch (e: Exception) {
                        0
                    }
                )
            }
        }

    // ----------------------------------------------------------------------

    private fun sorov(
        yol: String,
        metod: String,
        tana: String?,
        kalitsiz: Boolean = false,
    ): Javob<String> {
        if (asos.isBlank()) {
            return Javob.Xato(0, "Sayt manzili kiritilmagan")
        }
        if (!kalitsiz && kalit.isBlank()) {
            return Javob.Xato(0, "Qurilma saytga ulanmagan")
        }
        var ulanish: HttpURLConnection? = null
        return try {
            ulanish = (URL(asos + yol).openConnection() as HttpURLConnection).apply {
                requestMethod = metod
                connectTimeout = 15_000
                readTimeout = 25_000
                useCaches = false
                if (!kalitsiz) setRequestProperty("X-SMS-Kalit", kalit)
                setRequestProperty("Accept", "application/json")
                setRequestProperty("User-Agent", "KursSms (Android)")
                if (tana != null) {
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                }
            }
            if (tana != null) {
                ulanish.outputStream.use { it.write(tana.toByteArray(Charsets.UTF_8)) }
            }
            val kod = ulanish.responseCode
            val oqim = if (kod in 200..299) ulanish.inputStream else ulanish.errorStream
            val matn = oqim?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            when {
                kod in 200..299 -> Javob.Ok(matn)
                kod == 400 -> Javob.Xato(400, xatoSababi(matn) ?: "So'rov qabul qilinmadi")
                kod == 403 -> Javob.Xato(403, "Qurilma saytdan uzilgan - qayta ulaning")
                kod == 404 -> Javob.Xato(404, "Saytda SMS bo'limi o'chirilgan (yoki manzil xato)")
                kod in 500..599 -> Javob.Xato(kod, "Saytda xatolik ($kod)")
                else -> Javob.Xato(kod, "Sayt javobi: $kod")
            }
        } catch (e: Exception) {
            Javob.Xato(0, xatoMatni(e))
        } finally {
            ulanish?.disconnect()
        }
    }

    /** Sayt xatoni JSON ichida tushuntiradi: {"ok": false, "xato": "..."} */
    private fun xatoSababi(tana: String): String? = try {
        JSONObject(tana).optString("xato", "").ifBlank { null }
    } catch (e: Exception) {
        null
    }

    private fun xatoMatni(e: Exception): String = when (e) {
        is UnknownHostException -> "Sayt manzili topilmadi - internetni va manzilni tekshiring"
        is SocketTimeoutException -> "Sayt javob bermadi (vaqt tugadi)"
        is ConnectException -> "Saytga ulanib bo'lmadi - server o'chiqmi?"
        is SSLException -> "HTTPS xatosi: ${e.message ?: "sertifikat"}"
        is IOException -> "Aloqa uzildi: ${e.message ?: "tarmoq xatosi"}"
        else -> e.message ?: "Noma'lum xato"
    }
}
