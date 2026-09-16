package uz.olimjonov.kurssms.ish

import android.content.Context
import android.os.BatteryManager
import android.os.Build
import androidx.core.content.ContextCompat
import uz.olimjonov.kurssms.BuildConfig
import uz.olimjonov.kurssms.data.Jurnal
import uz.olimjonov.kurssms.data.Prefs
import uz.olimjonov.kurssms.sms.SimRoyxati
import uz.olimjonov.kurssms.tarmoq.Javob
import uz.olimjonov.kurssms.tarmoq.QurilmaMalumoti
import uz.olimjonov.kurssms.tarmoq.SaytApi

/**
 * Saytga ulanish: admin chiqargan 12 xonalik kod bilan bir marta ulanadi,
 * saytdan doimiy kalit oladi va uni telefonda saqlaydi.
 */
object Ulanish {

    /** Muvaffaqiyat bo'lsa `null`, aks holda xato matni qaytadi. */
    suspend fun ulan(context: Context, manzil: String, kod: String): String? {
        val tozaKod = kod.filter(Char::isDigit)
        if (tozaKod.length != 12) return "Kod 12 xonali bo'lishi kerak"

        val prefs = Prefs(context)
        val jurnal = Jurnal(context)
        prefs.manzil = manzil
        if (prefs.manzil.isBlank()) return "Sayt manzilini kiriting"

        val api = SaytApi(prefs.manzil)
        return when (val javob = api.ulan(tozaKod, qurilmaMalumoti(context, prefs))) {
            is Javob.Xato -> {
                jurnal.qosh("xato", "Ulanmadi: ${javob.xabar}")
                javob.xabar
            }

            is Javob.Ok -> {
                prefs.kalit = javob.qiymat.kalit
                prefs.saytNomi = javob.qiymat.sayt
                prefs.qurilmaNomi = javob.qiymat.qurilma
                jurnal.qosh("ok", "Saytga ulandi: ${javob.qiymat.sayt}")
                Bildirishnoma.ulandi(context, javob.qiymat.sayt)
                null
            }
        }
    }

    fun qurilmaMalumoti(context: Context, prefs: Prefs) = QurilmaMalumoti(
        qurilmaId = prefs.qurilmaId,
        nomi = qurilmaNomi(),
        ishlabChiqaruvchi = Build.MANUFACTURER ?: "",
        model = Build.MODEL ?: "",
        android = Build.VERSION.RELEASE ?: "",
        ilovaVersiya = BuildConfig.VERSIYA,
        simlar = SimRoyxati.royxat(context),
    )

    /** "samsung SM-A515F" -> "Samsung SM-A515F" */
    fun qurilmaNomi(): String {
        val ishlabChiqaruvchi = (Build.MANUFACTURER ?: "").trim()
        val model = (Build.MODEL ?: "").trim()
        val nomi = when {
            model.startsWith(ishlabChiqaruvchi, ignoreCase = true) -> model
            ishlabChiqaruvchi.isBlank() -> model
            else -> "$ishlabChiqaruvchi $model"
        }
        return nomi.replaceFirstChar { it.uppercase() }.ifBlank { "Telefon" }
    }

    /** Batareya foizi; aniqlanmasa -1. */
    fun batareya(context: Context): Int = try {
        ContextCompat.getSystemService(context, BatteryManager::class.java)
            ?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) ?: -1
    } catch (e: Exception) {
        -1
    }
}
