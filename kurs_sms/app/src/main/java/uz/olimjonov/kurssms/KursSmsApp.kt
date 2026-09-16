package uz.olimjonov.kurssms

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build

class KursSmsApp : Application() {

    override fun onCreate() {
        super.onCreate()
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

    companion object {
        const val KANAL = "kurs_sms"
    }
}
