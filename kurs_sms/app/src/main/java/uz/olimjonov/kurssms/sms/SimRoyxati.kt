package uz.olimjonov.kurssms.sms

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.telephony.SubscriptionManager
import androidx.core.content.ContextCompat

/** Telefondagi bitta SIM karta. */
data class Sim(
    val id: Int,
    val nomi: String,
    val raqam: String,
    val slot: Int = 0,
)

object SimRoyxati {

    /**
     * Faol SIM kartalar. Ruxsat berilmagan bo'lsa bo'sh ro'yxat qaytadi -
     * bunda ilova telefonning standart SIM kartasidan yuboradi.
     */
    fun royxat(context: Context): List<Sim> {
        if (!ruxsatBor(context)) return emptyList()
        return try {
            val manager = ContextCompat.getSystemService(context, SubscriptionManager::class.java)
                ?: return emptyList()
            @Suppress("MissingPermission")
            val royxat = manager.activeSubscriptionInfoList ?: return emptyList()
            royxat.map { malumot ->
                Sim(
                    id = malumot.subscriptionId,
                    nomi = malumot.displayName?.toString()?.ifBlank { null }
                        ?: "SIM ${malumot.simSlotIndex + 1}",
                    raqam = malumot.number ?: "",
                    slot = malumot.simSlotIndex,
                )
            }
        } catch (e: SecurityException) {
            emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    fun ruxsatBor(context: Context): Boolean =
        ContextCompat.checkSelfPermission(context, Manifest.permission.READ_PHONE_STATE) ==
            PackageManager.PERMISSION_GRANTED
}
