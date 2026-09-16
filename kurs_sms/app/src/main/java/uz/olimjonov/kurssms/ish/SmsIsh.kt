package uz.olimjonov.kurssms.ish

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import uz.olimjonov.kurssms.data.Prefs
import java.util.concurrent.TimeUnit

/**
 * Doimiy tekshiruv. WorkManager telefon qayta yoqilganda ham o'zi tiklaydi,
 * shuning uchun alohida doimiy xizmat (foreground service) kerak emas.
 *
 * Android da eng kichik takrorlanish oralig'i - 15 daqiqa.
 */
class SmsIsh(context: Context, parametrlar: WorkerParameters) :
    CoroutineWorker(context, parametrlar) {

    override suspend fun doWork(): Result {
        val prefs = Prefs(applicationContext)
        if (!prefs.yoqilgan) return Result.success()

        val xulosa = SinxronMotor(applicationContext).bajar()
        if (xulosa.jonatildi > 0 || xulosa.xato > 0) {
            Bildirishnoma.korsat(applicationContext, xulosa)
        }
        // Xato bo'lsa ham Result.retry() qilmaymiz: keyingi davriy urinish
        // baribir keladi, sayt esa xabarni yo'qotmaydi.
        return Result.success()
    }

    companion object {
        private const val NOM = "kurs_sms_tekshiruv"

        fun yoq(context: Context, oraliqDaqiqa: Int) {
            val cheklovlar = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val ish = PeriodicWorkRequestBuilder<SmsIsh>(
                oraliqDaqiqa.toLong().coerceAtLeast(15), TimeUnit.MINUTES
            )
                .setConstraints(cheklovlar)
                .setBackoffCriteria(BackoffPolicy.LINEAR, 5, TimeUnit.MINUTES)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                NOM, ExistingPeriodicWorkPolicy.UPDATE, ish
            )
        }

        fun ochir(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(NOM)
        }
    }
}
