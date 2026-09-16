package uz.olimjonov.kurssms.sms

import android.app.Activity
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.telephony.SmsManager
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference

/**
 * SMS ni telefonning SIM kartasidan jo'natadi va natijani kutadi.
 *
 * Android jo'natish natijasini broadcast orqali qaytaradi, shuning uchun
 * har bir xabarga alohida amal (action) nomi beriladi va natija kelguncha
 * kutiladi. Uzun matn bo'laklarga bo'linsa, hamma bo'lakning natijasi kutiladi.
 */
class SmsYuboruvchi(context: Context) {

    private val context = context.applicationContext

    /** Muvaffaqiyat bo'lsa `null`, aks holda xato matni qaytadi. */
    suspend fun yubor(telefon: String, matn: String, simId: Int): String? {
        val manager = smsManager(simId) ?: return "SMS xizmati topilmadi"

        val bolaklar = try {
            manager.divideMessage(matn)
        } catch (e: Exception) {
            return "Matnni bo'lishda xato: ${e.message}"
        }
        if (bolaklar.isNullOrEmpty()) return "Xabar matni bo'sh"

        val amal = "${context.packageName}.SMS_NATIJA.${hisoblagich.incrementAndGet()}"
        val natija = CompletableDeferred<String>()
        val qolgan = AtomicInteger(bolaklar.size)

        val xato = AtomicReference<String?>(null)
        val qabulQiluvchi = object : BroadcastReceiver() {
            override fun onReceive(c: Context?, i: Intent?) {
                if (resultCode != Activity.RESULT_OK) {
                    xato.compareAndSet(null, kodMatni(resultCode))
                }
                if (qolgan.decrementAndGet() <= 0) {
                    natija.complete(xato.get() ?: "")
                }
            }
        }

        ContextCompat.registerReceiver(
            context, qabulQiluvchi, IntentFilter(amal), ContextCompat.RECEIVER_NOT_EXPORTED
        )

        try {
            val niyatlar = ArrayList<PendingIntent>(bolaklar.size)
            for (indeks in bolaklar.indices) {
                niyatlar.add(
                    PendingIntent.getBroadcast(
                        context,
                        indeks,
                        Intent(amal).setPackage(context.packageName),
                        PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
                    )
                )
            }

            try {
                if (bolaklar.size == 1) {
                    manager.sendTextMessage(telefon, null, bolaklar[0], niyatlar[0], null)
                } else {
                    manager.sendMultipartTextMessage(telefon, null, bolaklar, niyatlar, null)
                }
            } catch (e: SecurityException) {
                return "SMS yuborish ruxsati berilmagan"
            } catch (e: IllegalArgumentException) {
                return "Telefon raqami noto'g'ri: $telefon"
            } catch (e: Exception) {
                return e.message ?: "Jo'natib bo'lmadi"
            }

            val javob = withTimeoutOrNull(KUTISH) { natija.await() }
            return when {
                javob == null -> "Javob kelmadi (vaqt tugadi)"
                javob.isEmpty() -> null
                else -> javob
            }
        } finally {
            try {
                context.unregisterReceiver(qabulQiluvchi)
            } catch (e: Exception) {
                // allaqachon olib tashlangan bo'lishi mumkin - muhim emas
            }
        }
    }

    @Suppress("DEPRECATION")
    private fun smsManager(simId: Int): SmsManager? = try {
        val asosiy = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            context.getSystemService(SmsManager::class.java)
        } else {
            SmsManager.getDefault()
        }
        when {
            simId < 0 -> asosiy
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
                asosiy?.createForSubscriptionId(simId)
            else -> SmsManager.getSmsManagerForSubscriptionId(simId)
        }
    } catch (e: Exception) {
        null
    }

    private fun kodMatni(kod: Int): String = when (kod) {
        SmsManager.RESULT_ERROR_GENERIC_FAILURE -> "Umumiy xato (operator qabul qilmadi)"
        SmsManager.RESULT_ERROR_RADIO_OFF -> "Telefon aloqasi o'chiq (parvoz rejimi?)"
        SmsManager.RESULT_ERROR_NULL_PDU -> "Xabar tayyorlanmadi"
        SmsManager.RESULT_ERROR_NO_SERVICE -> "Tarmoq yo'q - SIM da aloqa yo'q"
        SmsManager.RESULT_ERROR_LIMIT_EXCEEDED -> "Chegara oshdi - juda ko'p SMS yuborildi"
        SmsManager.RESULT_ERROR_FDN_CHECK_FAILURE -> "FDN cheklovi: raqamga ruxsat yo'q"
        SmsManager.RESULT_ERROR_SHORT_CODE_NOT_ALLOWED -> "Bu raqamga ruxsat berilmadi"
        else -> "Xato kodi: $kod"
    }

    companion object {
        private const val KUTISH = 90_000L
        private val hisoblagich = AtomicInteger(0)
    }
}
