package uz.olimjonov.kurssms

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.work.WorkManager

class KursSmsApp : Application() {

    override fun onCreate() {
        super.onCreate()
        eskiDavriyIshniBekorQil()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val kanal = NotificationChannel(
                KANAL,
                "SMS jo'natish",
                NotificationManager.IMPORTANCE_LOW,
            )
            kanal.description = "Jo'natilgan xabarlar va xatoliklar haqida xabar beradi"
            getSystemService(NotificationManager::class.java)
                ?.createNotificationChannel(kanal)
        }
    }

    /**
     * 1.2.0 gacha ilova har 15 daqiqada fonda uyg'onib saytga murojaat
     * qilardi. 1.3.0 dan boshlab bunday emas: ish faqat foydalanuvchi
     * "Ulanish" ni bosganda bajariladi.
     *
     * Eski o'rnatishlarda o'sha davriy vazifa rejalashtirilgan holda qolgan
     * bo'lishi mumkin - shu yerda bekor qilinadi.
     */
    private fun eskiDavriyIshniBekorQil() {
        try {
            WorkManager.getInstance(this).cancelUniqueWork(ESKI_ISH)
        } catch (e: Exception) {
            // WorkManager ishga tushmagan bo'lsa - e'tiborsiz qoldiramiz
        }
    }

    companion object {
        const val KANAL = "kurs_sms"
        private const val ESKI_ISH = "kurs_sms_tekshiruv"
    }
}
