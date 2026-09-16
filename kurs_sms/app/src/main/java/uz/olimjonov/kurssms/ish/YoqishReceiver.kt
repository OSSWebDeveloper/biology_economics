package uz.olimjonov.kurssms.ish

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import uz.olimjonov.kurssms.data.Prefs

/**
 * Telefon qayta yoqilganda yoki ilova yangilanganda davriy tekshiruvni tiklaydi.
 *
 * WorkManager buni odatda o'zi qiladi, lekin ba'zi qurilmalarda (ayniqsa
 * "tejamkor rejim" kuchli bo'lganlarida) ishonchliroq bo'lishi uchun qo'shildi.
 */
class YoqishReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val prefs = Prefs(context)
        if (prefs.yoqilgan && prefs.ulangan) {
            SmsIsh.yoq(context, prefs.oraliq)
        }
    }
}
