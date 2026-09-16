package uz.olimjonov.kurssms.ish

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import uz.olimjonov.kurssms.KursSmsApp
import uz.olimjonov.kurssms.MainActivity
import uz.olimjonov.kurssms.R
import uz.olimjonov.kurssms.data.Prefs

/**
 * Bitta jo'natish sessiyasi.
 *
 * Ilova fonda doimiy aylanib turmaydi - na batareyani, na saytning cheklangan
 * imkoniyatini bekorga yemaydi. Buning o'rniga:
 *
 *   1. Admin saytda xabarlarni qurilmaga beradi va "qabul oynasi" ni ochadi;
 *   2. Telefon egasi ilovada **Ulanish** ni bosadi - shu xizmat boshlanadi;
 *   3. Xizmat saytdan ish so'raydi (har [ORALIQ_MS]);
 *   4. Ish kelsa - SMS lar jo'natiladi, natija saytga qaytariladi, yangi
 *      xabar qolmagach xizmat **o'zi to'xtaydi**;
 *   5. [MUDDAT_DAQIQA] daqiqada ish kelmasa ham xizmat **o'zi to'xtaydi**.
 *
 * Keyingi jo'natishda telefon egasi yana **Ulanish** ni bosadi.
 *
 * Nega foreground xizmat: foydalanuvchi tugmani bosgani uchun Android bunga
 * ruxsat beradi, va telefon egasi ilovadan chiqib ketsa ham ish to'xtamaydi.
 * Muddat qisqa bo'lgani uchun Android 14/15 ning cheklovlariga tushmaydi.
 */
class SessiyaXizmati : Service() {

    private val doira = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var vazifa: Job? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, bayroqlar: Int, boshlashId: Int): Int {
        if (vazifa?.isActive == true) return START_NOT_STICKY   // allaqachon ishlayapti

        oldinga("Saytga ulanmoqda...")
        vazifa = doira.launch { aylanma() }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        vazifa?.cancel()
        doira.cancel()
        _holat.value = Holat()
        super.onDestroy()
    }

    // ----------------------------------------------------------------------

    private suspend fun aylanma() {
        val prefs = Prefs(applicationContext)
        if (!prefs.ulangan) {
            tugat("Qurilma saytga ulanmagan", muvaffaqiyatli = false)
            return
        }

        val motor = SinxronMotor(applicationContext)
        val tugash = SystemClock.elapsedRealtime() + MUDDAT_DAQIQA * 60_000L
        var jonatildi = 0
        var xato = 0
        var ishBolgan = false

        while (SystemClock.elapsedRealtime() < tugash) {
            val xulosa = motor.bajar()
            jonatildi += xulosa.jonatildi
            xato += xulosa.xato

            when {
                xulosa.ishBajarildi -> {
                    // Bitta to'plam jo'natildi. Yana qolgan bo'lishi mumkin -
                    // uzoq kutmasdan qayta so'raymiz.
                    ishBolgan = true
                    holatniYoz(tugash, "$jonatildi ta jo'natildi", jonatildi, xato)
                    oldinga("$jonatildi ta jo'natildi, yana tekshirilmoqda...")
                    delay(ISHDAN_KEYIN_MS)
                }

                ishBolgan -> {
                    // Ish bajarildi va yangi xabar qolmadi - sessiya tugadi.
                    break
                }

                else -> {
                    val matn = if (xulosa.yopiq) {
                        "Sayt hali qabul qilmayapti - kutilmoqda"
                    } else {
                        xulosa.xabar
                    }
                    holatniYoz(tugash, matn, jonatildi, xato)
                    oldinga(matn)
                    delay(ORALIQ_MS)
                }
            }
        }

        val yakun = when {
            jonatildi > 0 && xato == 0 -> "$jonatildi ta SMS jo'natildi"
            jonatildi > 0 -> "$jonatildi ta jo'natildi, $xato ta xato"
            xato > 0 -> "$xato ta xabar jo'natilmadi"
            else -> "$MUDDAT_DAQIQA daqiqada ish kelmadi"
        }
        if (jonatildi > 0 || xato > 0) {
            Bildirishnoma.korsat(
                applicationContext,
                SinxronMotor.Xulosa(jonatildi, xato, yakun, xato == 0),
            )
        }
        tugat(yakun, muvaffaqiyatli = xato == 0)
    }

    private fun holatniYoz(tugash: Long, matn: String, jonatildi: Int, xato: Int) {
        val qolgan = ((tugash - SystemClock.elapsedRealtime()) / 1000).toInt().coerceAtLeast(0)
        _holat.value = Holat(
            ishlayapti = true,
            qolganSoniya = qolgan,
            matn = matn,
            jonatildi = jonatildi,
            xato = xato,
        )
    }

    private fun tugat(matn: String, muvaffaqiyatli: Boolean) {
        _holat.value = Holat(ishlayapti = false, matn = matn, muvaffaqiyatli = muvaffaqiyatli)
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    // ----------------------------------------------------------------------

    private fun oldinga(matn: String) {
        val bildirishnoma = qur(matn)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(ID, bildirishnoma, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(ID, bildirishnoma)
        }
    }

    private fun qur(matn: String): Notification {
        val niyat = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        return NotificationCompat.Builder(this, KursSmsApp.KANAL)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Kurs SMS ishlayapti")
            .setContentText(matn)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .setContentIntent(niyat)
            .build()
    }

    // ----------------------------------------------------------------------

    /** Ekranda ko'rsatish uchun sessiyaning hozirgi holati. */
    data class Holat(
        val ishlayapti: Boolean = false,
        val qolganSoniya: Int = 0,
        val matn: String = "",
        val jonatildi: Int = 0,
        val xato: Int = 0,
        val muvaffaqiyatli: Boolean = true,
    ) {
        val qolganMatni: String
            get() {
                val daqiqa = qolganSoniya / 60
                val soniya = qolganSoniya % 60
                return "$daqiqa:${soniya.toString().padStart(2, '0')}"
            }
    }

    companion object {
        /** Ish kelmasa sessiya shuncha daqiqadan keyin o'zi to'xtaydi. */
        const val MUDDAT_DAQIQA = 15

        /** Ish yo'q paytdagi so'rov oralig'i. */
        private const val ORALIQ_MS = 30_000L

        /** Bir to'plam jo'natilgandan keyin qayta so'rashgacha. */
        private const val ISHDAN_KEYIN_MS = 5_000L

        private const val ID = 7003

        private val _holat = MutableStateFlow(Holat())
        val holat: StateFlow<Holat> = _holat.asStateFlow()

        fun boshla(context: Context) {
            ContextCompat.startForegroundService(
                context, Intent(context, SessiyaXizmati::class.java)
            )
        }

        fun toxtat(context: Context) {
            context.stopService(Intent(context, SessiyaXizmati::class.java))
        }
    }
}
