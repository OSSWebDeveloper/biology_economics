package uz.olimjonov.kurssms.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import uz.olimjonov.kurssms.BuildConfig
import uz.olimjonov.kurssms.data.Jurnal
import uz.olimjonov.kurssms.data.Prefs
import uz.olimjonov.kurssms.data.Yozuv
import uz.olimjonov.kurssms.ish.SinxronMotor
import uz.olimjonov.kurssms.ish.SessiyaXizmati
import uz.olimjonov.kurssms.ish.Ulanish
import uz.olimjonov.kurssms.sms.Sim
import uz.olimjonov.kurssms.sms.SimRoyxati
import uz.olimjonov.kurssms.tarmoq.Javob
import uz.olimjonov.kurssms.tarmoq.SaytApi

class AsosiyViewModel(ilova: Application) : AndroidViewModel(ilova) {

    private val kontekst = ilova.applicationContext
    private val prefs = Prefs(kontekst)
    private val jurnal = Jurnal(kontekst)

    data class Holat(
        val manzil: String = "",
        val ulangan: Boolean = false,
        val saytNomi: String = "",
        val qurilmaNomi: String = "",
        val oraliq: Int = 15,
        val tanaffus: Int = 4,
        val birMartada: Int = 10,
        val yoqilgan: Boolean = false,
        val simlar: List<Sim> = emptyList(),
        val yozuvlar: List<Yozuv> = emptyList(),
        val oxirgiTekshiruv: Long = 0L,
        val oxirgiNatija: String = "",
        val ishlamoqda: Boolean = false,
        val xabar: String = "",
        val yaxshi: Boolean? = null,
        val versiya: String = BuildConfig.VERSIYA,
        val engYangiVersiya: String = "",
    ) {
        /** Saytda yangiroq versiya bormi. */
        val yangilanishBor: Boolean
            get() = engYangiVersiya.isNotBlank() &&
                Prefs.versiyaRaqami(engYangiVersiya) > Prefs.versiyaRaqami(versiya)
    }

    var holat by mutableStateOf(Holat())
        private set

    init {
        yangila()
    }

    fun yangila() {
        holat = holat.copy(
            manzil = prefs.manzil,
            ulangan = prefs.ulangan,
            saytNomi = prefs.saytNomi,
            qurilmaNomi = prefs.qurilmaNomi,
            oraliq = prefs.oraliq,
            tanaffus = prefs.tanaffus,
            birMartada = prefs.birMartada,
            yoqilgan = prefs.yoqilgan,
            simlar = SimRoyxati.royxat(kontekst),
            yozuvlar = jurnal.royxat(),
            oxirgiTekshiruv = prefs.oxirgiTekshiruv,
            oxirgiNatija = prefs.oxirgiNatija,
            engYangiVersiya = prefs.engYangiVersiya,
        )
    }

    // ---------------------------------------------------------------- ulanish

    /** 12 xonalik kod bilan saytga ulanish. */
    fun ulan(manzil: String, kod: String) {
        if (holat.ishlamoqda) return
        holat = holat.copy(ishlamoqda = true, xabar = "", yaxshi = null)
        viewModelScope.launch {
            val xato = Ulanish.ulan(kontekst, manzil, kod)
            yangila()
            holat = if (xato == null) {
                // Ulangandan keyin avtomatik tekshirish o'zi yoqiladi
                prefs.yoqilgan = true
                yangila()
                holat.copy(
                    ishlamoqda = false,
                    yaxshi = true,
                    xabar = "Saytga ulandi" +
                        if (prefs.saytNomi.isNotBlank()) ": ${prefs.saytNomi}" else "",
                )
            } else {
                holat.copy(ishlamoqda = false, yaxshi = false, xabar = xato)
            }
        }
    }

    /** Saytdan uzilish (kalit o'chiriladi, qaytadan kod bilan ulanadi). */
    fun uzil() {
        prefs.ulanishniOchir()
        prefs.yoqilgan = false
        SessiyaXizmati.toxtat(kontekst)
        jurnal.qosh("malumot", "Saytdan uzildi")
        yangila()
        holat = holat.copy(xabar = "Saytdan uzildi", yaxshi = null)
    }

    // ------------------------------------------------------------- sozlamalar

    fun saqla(manzil: String, oraliq: Int, tanaffus: Int, birMartada: Int) {
        prefs.manzil = manzil
        prefs.oraliq = oraliq
        prefs.tanaffus = tanaffus
        prefs.birMartada = birMartada
        yangila()
    }

    fun yoqOchir(yoq: Boolean) {
        prefs.yoqilgan = yoq
        if (!yoq) SessiyaXizmati.toxtat(kontekst)
        yangila()
    }

    // ------------------------------------------------------------- sessiya

    /**
     * Jo'natish sessiyasini boshlaydi.
     *
     * Ilova fonda aylanib turmaydi: telefon egasi har safar jo'natish kerak
     * bo'lganda shu tugmani bosadi. Xizmat ishini bajarib bo'lgach yoki
     * [SessiyaXizmati.MUDDAT_DAQIQA] daqiqada ish kelmasa o'zi to'xtaydi.
     */
    fun sessiyaniBoshla() {
        if (!prefs.ulangan) {
            holat = holat.copy(yaxshi = false, xabar = "Avval saytga ulaning")
            return
        }
        SessiyaXizmati.boshla(kontekst)
        holat = holat.copy(xabar = "", yaxshi = null)
    }

    fun sessiyaniToxtat() {
        SessiyaXizmati.toxtat(kontekst)
    }

    // ---------------------------------------------------------------- amallar

    fun ulanishniTekshir() {
        if (holat.ishlamoqda) return
        holat = holat.copy(ishlamoqda = true, xabar = "", yaxshi = null)
        viewModelScope.launch {
            val api = SaytApi(prefs.manzil, prefs.kalit)
            val javob = api.tekshir(Ulanish.batareya(kontekst), BuildConfig.VERSIYA)
            holat = when (javob) {
                is Javob.Ok -> {
                    prefs.engYangiVersiya = javob.qiymat.engYangiVersiya
                    yangila()
                    holat.copy(
                        ishlamoqda = false,
                        yaxshi = true,
                        xabar = buildString {
                            append("Aloqa yaxshi")
                            if (javob.qiymat.sayt.isNotBlank()) append(" - ${javob.qiymat.sayt}")
                            append(". Sizga ${javob.qiymat.navbatda} ta xabar berilgan.")
                        },
                    )
                }

                is Javob.Xato -> holat.copy(
                    ishlamoqda = false,
                    yaxshi = false,
                    xabar = javob.xabar,
                )
            }
        }
    }

    fun hozirTekshir() {
        if (holat.ishlamoqda) return
        holat = holat.copy(ishlamoqda = true, xabar = "", yaxshi = null)
        viewModelScope.launch {
            val xulosa = SinxronMotor(kontekst).bajar()
            yangila()
            holat = holat.copy(
                ishlamoqda = false,
                yaxshi = xulosa.muvaffaqiyatli,
                xabar = xulosa.xabar,
            )
        }
    }

    /** SIM ro'yxatini saytga qayta yuborish (SIM almashtirilganda). */
    fun simlarniYubor() {
        if (holat.ishlamoqda) return
        holat = holat.copy(ishlamoqda = true, xabar = "", yaxshi = null)
        viewModelScope.launch {
            val ok = SinxronMotor(kontekst).simlarniYubor()
            yangila()
            holat = holat.copy(
                ishlamoqda = false,
                yaxshi = ok,
                xabar = if (ok) "SIM ro'yxati saytga yuborildi"
                else "SIM ro'yxati yuborilmadi",
            )
        }
    }

    fun jurnalniTozala() {
        jurnal.tozala()
        yangila()
    }
}
