package uz.olimjonov.kurssms

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.viewmodel.compose.viewModel
import uz.olimjonov.kurssms.ish.SessiyaXizmati
import uz.olimjonov.kurssms.ui.AsosiyViewModel
import uz.olimjonov.kurssms.ui.ekran.BoshEkran
import uz.olimjonov.kurssms.ui.ekran.SozlamaEkran
import uz.olimjonov.kurssms.ui.theme.KursSmsTheme

/** Tashqaridan (TELEFONGA.bat skriptidan) kelgan ulanish taklifi. */
data class UlanishSorovi(val manzil: String, val kod: String)

class MainActivity : ComponentActivity() {

    /**
     * Kompyuterdagi skript ilovani shunday ochadi:
     *
     *   adb shell am start -n uz.olimjonov.kurssms/.MainActivity \
     *       --es manzil 'https://kurs.example.uz' --es kod '049125081866'
     *
     * Shunda 12 raqamni telefonda qo'lda terish kerak emas. Lekin ulanish
     * O'Z-O'ZIDAN bo'lmaydi: ekranda "qaysi saytga ulanamiz" deb tasdiq
     * so'raladi - boshqa biror ilova soxta manzil bilan ulab yubormasligi uchun.
     */
    private var sorov by mutableStateOf<UlanishSorovi?>(null)

    override fun onCreate(saqlangan: Bundle?) {
        super.onCreate(saqlangan)
        sorov = sorovniOqi(intent)

        setContent {
            KursSmsTheme {
                Surface(
                    modifier = Modifier,
                    color = MaterialTheme.colorScheme.background,
                ) {
                    Ilova(
                        sorov = sorov,
                        onSorovYopildi = { sorov = null },
                    )
                }
            }
        }
    }

    override fun onNewIntent(yangi: Intent) {
        super.onNewIntent(yangi)
        setIntent(yangi)
        sorovniOqi(yangi)?.let { sorov = it }
    }

    private fun sorovniOqi(niyat: Intent?): UlanishSorovi? {
        val kod = (niyat?.getStringExtra("kod") ?: "").filter(Char::isDigit)
        if (kod.length != 12) return null
        return UlanishSorovi(
            manzil = (niyat?.getStringExtra("manzil") ?: "").trim(),
            kod = kod,
        )
    }
}

@Composable
private fun Ilova(
    sorov: UlanishSorovi?,
    onSorovYopildi: () -> Unit,
    vm: AsosiyViewModel = viewModel(),
) {
    val kontekst = LocalContext.current
    var ekran by remember { mutableStateOf("bosh") }
    var yangilanish by remember { mutableIntStateOf(0) }

    // Ilovaga qaytilganda (masalan sozlamalardan) holat qayta o'qiladi
    val hayotOwner = LocalLifecycleOwner.current
    DisposableEffect(hayotOwner) {
        val kuzatuvchi = LifecycleEventObserver { _, hodisa ->
            if (hodisa == Lifecycle.Event.ON_RESUME) {
                yangilanish++
                vm.yangila()
            }
        }
        hayotOwner.lifecycle.addObserver(kuzatuvchi)
        onDispose { hayotOwner.lifecycle.removeObserver(kuzatuvchi) }
    }

    val soruvchi = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        yangilanish++
        vm.yangila()
    }

    // Birinchi ochilganda kerakli ruxsatlar so'raladi
    LaunchedEffect(Unit) {
        val kerakli = mutableListOf(Manifest.permission.SEND_SMS)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            kerakli.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        val yetishmayotgan = kerakli.filter { !ruxsatBor(kontekst, it) }
        if (yetishmayotgan.isNotEmpty()) soruvchi.launch(yetishmayotgan.toTypedArray())
    }

    val smsRuxsat = remember(yangilanish) {
        ruxsatBor(kontekst, Manifest.permission.SEND_SMS)
    }
    val batareyaErkin = remember(yangilanish) { batareyaErkinmi(kontekst) }

    // Skriptdan kelgan ulanish taklifi - tasdiq so'raladi
    if (sorov != null) {
        val manzil = sorov.manzil.ifBlank { vm.holat.manzil }
        UlanishOynasi(
            manzil = manzil,
            kod = sorov.kod,
            allaqachonUlangan = vm.holat.ulangan,
            onUlan = {
                vm.ulan(manzil, sorov.kod)
                onSorovYopildi()
            },
            onBekor = onSorovYopildi,
        )
    }

    when (ekran) {
        "sozlama" -> SozlamaEkran(
            holat = vm.holat,
            onUlan = { manzil, kod -> vm.ulan(manzil, kod) },
            onUzil = { vm.uzil() },
            onSaqla = { manzil, oraliq, tanaffus, birMartada ->
                vm.saqla(manzil, oraliq, tanaffus, birMartada)
            },
            onTekshir = { vm.ulanishniTekshir() },
            onSimYubor = { vm.simlarniYubor() },
            onSimRuxsat = { soruvchi.launch(arrayOf(Manifest.permission.READ_PHONE_STATE)) },
            onOrqaga = { ekran = "bosh" },
        )

        else -> BoshEkran(
            holat = vm.holat,
            sessiya = SessiyaXizmati.holat.collectAsState().value,
            smsRuxsat = smsRuxsat,
            batareyaErkin = batareyaErkin,
            onRuxsatSora = { soruvchi.launch(arrayOf(Manifest.permission.SEND_SMS)) },
            onBatareya = { batareyaniSora(kontekst) },
            onSozlama = { ekran = "sozlama" },
            onYoqOchir = { vm.yoqOchir(it) },
            onSessiyaBoshla = { vm.sessiyaniBoshla() },
            onSessiyaToxtat = { vm.sessiyaniToxtat() },
            onHozirTekshir = { vm.hozirTekshir() },
            onTozala = { vm.jurnalniTozala() },
        )
    }
}

@Composable
private fun UlanishOynasi(
    manzil: String,
    kod: String,
    allaqachonUlangan: Boolean,
    onUlan: () -> Unit,
    onBekor: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onBekor,
        title = { Text("Saytga ulanish") },
        text = {
            Text(
                buildString {
                    append("Kompyuterdan ulanish so'rovi keldi.\n\n")
                    append("Sayt: ")
                    append(manzil.ifBlank { "(kiritilmagan)" })
                    append("\nKod: ")
                    append(kod.chunked(4).joinToString(" "))
                    if (allaqachonUlangan) {
                        append("\n\nDIQQAT: qurilma allaqachon ulangan. ")
                        append("Yangi ulanish eskisining o'rnini egallaydi.")
                    }
                }
            )
        },
        confirmButton = {
            TextButton(onClick = onUlan, enabled = manzil.isNotBlank()) {
                Text("Ulanish")
            }
        },
        dismissButton = {
            TextButton(onClick = onBekor) { Text("Bekor qilish") }
        },
    )
}

private fun ruxsatBor(kontekst: Context, ruxsat: String): Boolean =
    ContextCompat.checkSelfPermission(kontekst, ruxsat) == PackageManager.PERMISSION_GRANTED

private fun batareyaErkinmi(kontekst: Context): Boolean = try {
    ContextCompat.getSystemService(kontekst, PowerManager::class.java)
        ?.isIgnoringBatteryOptimizations(kontekst.packageName) ?: true
} catch (e: Exception) {
    true
}

private fun batareyaniSora(kontekst: Context) {
    val niyatlar = listOf(
        Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            .setData(Uri.parse("package:${kontekst.packageName}")),
        Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS),
    )
    for (niyat in niyatlar) {
        try {
            niyat.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            kontekst.startActivity(niyat)
            return
        } catch (e: Exception) {
            // keyingisini sinab ko'ramiz
        }
    }
}
