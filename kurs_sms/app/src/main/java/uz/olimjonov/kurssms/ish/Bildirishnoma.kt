package uz.olimjonov.kurssms.ish

import android.Manifest
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import uz.olimjonov.kurssms.KursSmsApp
import uz.olimjonov.kurssms.MainActivity
import uz.olimjonov.kurssms.R

object Bildirishnoma {

    /** Tekshiruvda biror narsa sodir bo'lsa (SMS ketdi yoki xato) xabar beradi. */
    fun korsat(context: Context, xulosa: SinxronMotor.Xulosa) {
        val sarlavha = when {
            xulosa.jonatildi > 0 && xulosa.xato == 0 -> "${xulosa.jonatildi} ta SMS jo'natildi"
            xulosa.jonatildi > 0 -> "${xulosa.jonatildi} ta jo'natildi, ${xulosa.xato} ta xato"
            xulosa.xato > 0 -> "SMS jo'natilmadi"
            else -> "Kurs SMS"
        }
        chiqar(context, ID, sarlavha, xulosa.xabar)
    }

    /** Saytga ulanish muvaffaqiyatli bo'lganda (saytda ham shunday xabar chiqadi). */
    fun ulandi(context: Context, sayt: String) {
        chiqar(
            context,
            ULANISH_ID,
            "Saytga ulandi",
            if (sayt.isBlank()) "Qurilma saytga muvaffaqiyatli ulandi."
            else "Qurilma \"$sayt\" saytiga ulandi. Endi SMS xabarlarni jo'nata oladi.",
        )
    }

    private fun chiqar(context: Context, id: Int, sarlavha: String, matn: String) {
        if (!ruxsatBor(context)) return

        val niyat = PendingIntent.getActivity(
            context,
            0,
            Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )

        val bildirishnoma = NotificationCompat.Builder(context, KursSmsApp.KANAL)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(sarlavha)
            .setContentText(matn)
            .setStyle(NotificationCompat.BigTextStyle().bigText(matn))
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setAutoCancel(true)
            .setContentIntent(niyat)
            .build()

        try {
            ContextCompat.getSystemService(context, NotificationManager::class.java)
                ?.notify(id, bildirishnoma)
        } catch (e: SecurityException) {
            // ruxsat bekor qilingan bo'lishi mumkin - e'tiborsiz qoldiramiz
        }
    }

    private fun ruxsatBor(context: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(
                context, Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED

    private const val ID = 7001
    private const val ULANISH_ID = 7002
}
