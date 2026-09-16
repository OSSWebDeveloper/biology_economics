package uz.olimjonov.kurssms.ish

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import kotlinx.coroutines.delay
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import uz.olimjonov.kurssms.BuildConfig
import uz.olimjonov.kurssms.data.Jurnal
import uz.olimjonov.kurssms.data.Prefs
import uz.olimjonov.kurssms.data.Yuborilganlar
import uz.olimjonov.kurssms.sms.Sim
import uz.olimjonov.kurssms.sms.SimRoyxati
import uz.olimjonov.kurssms.sms.SmsYuboruvchi
import uz.olimjonov.kurssms.tarmoq.Javob
import uz.olimjonov.kurssms.tarmoq.SaytApi
import uz.olimjonov.kurssms.tarmoq.YuborishNatijasi

/**
 * Bitta tekshiruv sikli:
 *   1. Saytga "men tirikman" signali (aloqa + batareya + versiya)
 *   1a. SIM ro'yxati o'zgargan bo'lsa - saytga yetkazadi (o'zi, tugmasiz)
 *   2. O'ziga berilgan xabarlarni oladi
 *   3. Har birini kerakli SIM kartadan jo'natadi
 *   4. Natijani saytga qaytaradi
 *
 * Bir vaqtda faqat bitta sikl ishlaydi (qo'lda bosilgan "Hozir tekshirish"
 * avtomatik tekshiruv bilan to'qnashmasligi uchun).
 */
class SinxronMotor(context: Context) {

    private val context = context.applicationContext
    private val prefs = Prefs(this.context)
    private val jurnal = Jurnal(this.context)
    private val yuborilganlar = Yuborilganlar(this.context)
    private val yuboruvchi = SmsYuboruvchi(this.context)

    data class Xulosa(
        val jonatildi: Int = 0,
        val xato: Int = 0,
        val xabar: String = "",
        val muvaffaqiyatli: Boolean = true,
        /** Sayt hozir qurilmalarni qabul qilmayapti (xato emas - kutish kerak). */
        val yopiq: Boolean = false,
    ) {
        /** Shu siklda biror ish bajarildimi. */
        val ishBajarildi: Boolean get() = jonatildi > 0 || xato > 0
    }

    suspend fun bajar(): Xulosa = qulf.withLock {
        val xulosa = ishla()
        prefs.oxirgiTekshiruv = System.currentTimeMillis()
        prefs.oxirgiNatija = xulosa.xabar
        xulosa
    }

    private suspend fun ishla(): Xulosa {
        if (!prefs.ulangan) {
            return Xulosa(xabar = "Qurilma saytga ulanmagan", muvaffaqiyatli = false)
        }
        if (!smsRuxsatiBor()) {
            val matn = "SMS yuborish ruxsati berilmagan"
            jurnal.qosh("xato", matn)
            return Xulosa(xabar = matn, muvaffaqiyatli = false)
        }

        val api = SaytApi(prefs.manzil, prefs.kalit)

        // 1) Aloqa signali - saytda "onlayn" bo'lib turish uchun
        when (val holat = api.tekshir(Ulanish.batareya(context), BuildConfig.VERSIYA)) {
            is Javob.Xato -> {
                jurnal.qosh("xato", holat.xabar)
                return Xulosa(xabar = holat.xabar, muvaffaqiyatli = false)
            }

            is Javob.Ok -> {
                prefs.engYangiVersiya = holat.qiymat.engYangiVersiya
                if (holat.qiymat.qurilma.isNotBlank()) {
                    prefs.qurilmaNomi = holat.qiymat.qurilma
                }
                // Admin saytda "qabul oynasi" ni ochmagan - hozircha ish yo'q.
                // Bu xato emas: navbatni ham so'ramaymiz, kutamiz.
                if (holat.qiymat.yopiq) {
                    return Xulosa(
                        xabar = "Sayt hali qabul qilmayapti",
                        yopiq = true,
                    )
                }
            }
        }

        // 1a) SIM ro'yxati - o'zgargan bo'lsa saytga o'zi ketadi
        simlarniSinxronla(api)

        // 2) Navbat
        val xabarlar = when (val javob = api.navbat(prefs.birMartada)) {
            is Javob.Xato -> {
                jurnal.qosh("xato", javob.xabar)
                return Xulosa(xabar = javob.xabar, muvaffaqiyatli = false)
            }

            is Javob.Ok -> javob.qiymat
        }

        if (xabarlar.isEmpty()) {
            return Xulosa(xabar = "Yangi xabar yo'q")
        }

        // 3) Jo'natish
        val natijalar = ArrayList<YuborishNatijasi>(xabarlar.size)
        var jonatildi = 0
        var xato = 0

        for ((indeks, xabar) in xabarlar.withIndex()) {
            if (yuborilganlar.bormi(xabar.id)) {
                // Oldingi safar jo'natilgan, lekin natijasi saytga yetib bormagan.
                jurnal.qosh("malumot", "${xabar.telefon} - allaqachon jo'natilgan, takrorlanmadi")
                natijalar.add(YuborishNatijasi(xabar.id, true))
                continue
            }

            val xatoMatni = yuboruvchi.yubor(xabar.telefon, xabar.matn, xabar.sim)
            if (xatoMatni == null) {
                yuborilganlar.qosh(xabar.id)
                jurnal.qosh("ok", "${xabar.telefon} - jo'natildi")
                natijalar.add(YuborishNatijasi(xabar.id, true))
                jonatildi++
            } else {
                jurnal.qosh("xato", "${xabar.telefon} - $xatoMatni")
                natijalar.add(YuborishNatijasi(xabar.id, false, xatoMatni))
                xato++
            }

            if (indeks < xabarlar.size - 1 && prefs.tanaffus > 0) {
                delay(prefs.tanaffus * 1000L)
            }
        }

        // 4) Natijani saytga qaytarish. Yetib bormasa ham qo'rqinchli emas:
        // sayt xabarni keyin qaytadan beradi, ilova esa uni takror jo'natmaydi.
        val qaytarish = api.holat(natijalar)
        if (qaytarish is Javob.Xato) {
            jurnal.qosh("xato", "Natija saytga yetkazilmadi: ${qaytarish.xabar}")
        }

        val xabar = buildString {
            append("$jonatildi ta jo'natildi")
            if (xato > 0) append(", $xato ta xato")
        }
        jurnal.qosh(if (xato > 0) "xato" else "ok", xabar)
        return Xulosa(jonatildi, xato, xabar, xato == 0)
    }

    /**
     * SIM ro'yxatini saytga yetkazadi - FAQAT oxirgi yuborilganidan farq
     * qilsa. Shu sababli har 15 daqiqada ortiqcha so'rov ketmaydi, lekin
     * SIM almashtirilsa sayt keyingi tekshiruvdayoq biladi.
     */
    private suspend fun simlarniSinxronla(api: SaytApi) {
        val simlar = SimRoyxati.royxat(context)
        if (simlar.isEmpty()) return
        val imzo = imzo(simlar)
        if (imzo == prefs.simlarImzosi) return

        if (api.simlarniYubor(simlar) is Javob.Ok) {
            prefs.simlarImzosi = imzo
            jurnal.qosh("malumot", "SIM ro'yxati saytga yuborildi (${simlar.size} ta)")
        }
    }

    /** SIM ro'yxatining o'zgarganini bilish uchun qisqa belgi. */
    private fun imzo(simlar: List<Sim>): String =
        simlar.sortedBy { it.id }
            .joinToString("|") { "${it.id}:${it.nomi}:${it.raqam}:${it.slot}" }

    /** "SIM larni yuborish" tugmasi uchun - o'zgarmagan bo'lsa ham yuboradi. */
    suspend fun simlarniYubor(): Boolean {
        if (!prefs.ulangan) return false
        val simlar = SimRoyxati.royxat(context)
        if (simlar.isEmpty()) return false
        val javob = SaytApi(prefs.manzil, prefs.kalit).simlarniYubor(simlar)
        if (javob is Javob.Ok) prefs.simlarImzosi = imzo(simlar)
        return javob is Javob.Ok
    }

    private fun smsRuxsatiBor(): Boolean =
        ContextCompat.checkSelfPermission(context, Manifest.permission.SEND_SMS) ==
            PackageManager.PERMISSION_GRANTED

    companion object {
        private val qulf = Mutex()
    }
}
