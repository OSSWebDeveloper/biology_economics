@file:OptIn(ExperimentalMaterial3Api::class)

package uz.olimjonov.kurssms.ui.ekran

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.material3.TopAppBar
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import uz.olimjonov.kurssms.ui.AsosiyViewModel
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun BoshEkran(
    holat: AsosiyViewModel.Holat,
    smsRuxsat: Boolean,
    batareyaErkin: Boolean,
    onRuxsatSora: () -> Unit,
    onBatareya: () -> Unit,
    onSozlama: () -> Unit,
    onYoqOchir: (Boolean) -> Unit,
    onHozirTekshir: () -> Unit,
    onTozala: () -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Kurs SMS") },
                actions = {
                    IconButton(onClick = onSozlama) {
                        Icon(Icons.Filled.Settings, contentDescription = "Sozlamalar")
                    }
                },
            )
        }
    ) { chekka ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(chekka)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Spacer(Modifier.height(4.dp))

            if (!holat.ulangan) {
                Ogohlantirish(
                    matn = "Qurilma saytga ulanmagan. Saytdagi \"Xabarnoma\" bo'limidan " +
                        "12 xonalik ulanish kodini oling.",
                    tugma = "Ulanish",
                    onBos = onSozlama,
                )
            }

            if (!smsRuxsat) {
                Ogohlantirish(
                    matn = "SMS yuborish ruxsati berilmagan - ilova xabar jo'nata olmaydi.",
                    tugma = "Ruxsat berish",
                    onBos = onRuxsatSora,
                )
            }

            if (holat.ulangan && !batareyaErkin) {
                Ogohlantirish(
                    matn = "Batareya tejash rejimi yoqilgan. Telefon uzoq ishlatilmasa " +
                        "tekshiruv kechikishi mumkin.",
                    tugma = "Ruxsat berish",
                    onBos = onBatareya,
                )
            }

            if (holat.yangilanishBor) {
                Ogohlantirish(
                    matn = "Ilovaning yangi versiyasi bor: v${holat.engYangiVersiya} " +
                        "(sizda v${holat.versiya}). Yangi APK ni o'rnating.",
                    tugma = null,
                    onBos = {},
                )
            }

            HolatKartasi(holat, onYoqOchir)

            Button(
                onClick = onHozirTekshir,
                enabled = !holat.ishlamoqda && holat.ulangan,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (holat.ishlamoqda) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary,
                    )
                    Spacer(Modifier.size(8.dp))
                    Text("Tekshirilmoqda...")
                } else {
                    Icon(Icons.Filled.Refresh, contentDescription = null)
                    Spacer(Modifier.size(8.dp))
                    Text("Hozir tekshirish")
                }
            }

            if (holat.xabar.isNotBlank()) {
                Text(
                    text = holat.xabar,
                    style = MaterialTheme.typography.bodyMedium,
                    color = when (holat.yaxshi) {
                        true -> MaterialTheme.colorScheme.primary
                        false -> MaterialTheme.colorScheme.error
                        null -> MaterialTheme.colorScheme.onSurface
                    },
                )
            }

            HorizontalDivider()

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text("Jurnal", style = MaterialTheme.typography.titleMedium)
                if (holat.yozuvlar.isNotEmpty()) {
                    TextButton(onClick = onTozala) { Text("Tozalash") }
                }
            }

            if (holat.yozuvlar.isEmpty()) {
                Text(
                    "Hozircha yozuv yo'q.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    items(holat.yozuvlar) { yozuv ->
                        Row(modifier = Modifier.fillMaxWidth()) {
                            Text(
                                text = vaqtMatni(yozuv.vaqt),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(end = 8.dp),
                            )
                            Text(
                                text = yozuv.matn,
                                style = MaterialTheme.typography.bodySmall,
                                color = when (yozuv.turi) {
                                    "ok" -> MaterialTheme.colorScheme.primary
                                    "xato" -> MaterialTheme.colorScheme.error
                                    else -> MaterialTheme.colorScheme.onSurface
                                },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun HolatKartasi(
    holat: AsosiyViewModel.Holat,
    onYoqOchir: (Boolean) -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        ),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            if (holat.ulangan) {
                Text(
                    text = holat.saytNomi.ifBlank { "Saytga ulangan" },
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
                if (holat.qurilmaNomi.isNotBlank()) {
                    Text(
                        text = "Bu qurilma: ${holat.qurilmaNomi}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
                Spacer(Modifier.height(10.dp))
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = if (holat.yoqilgan) "Avtomatik tekshirish yoqilgan"
                        else "Avtomatik tekshirish o'chiq",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Text(
                        text = "Har ${holat.oraliq} daqiqada saytdan yangi xabar so'raladi",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
                Switch(
                    checked = holat.yoqilgan,
                    onCheckedChange = onYoqOchir,
                    enabled = holat.ulangan,
                )
            }

            Spacer(Modifier.height(10.dp))

            Text(
                text = if (holat.oxirgiTekshiruv > 0) {
                    "Oxirgi tekshiruv: ${toliqVaqt(holat.oxirgiTekshiruv)}" +
                        if (holat.oxirgiNatija.isNotBlank()) " - ${holat.oxirgiNatija}" else ""
                } else {
                    "Hali tekshirilmagan"
                },
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
private fun Ogohlantirish(matn: String, tugma: String?, onBos: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.errorContainer
        ),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                text = matn,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onErrorContainer,
            )
            if (tugma != null) {
                Spacer(Modifier.height(6.dp))
                OutlinedButton(onClick = onBos) { Text(tugma) }
            }
        }
    }
}

private fun vaqtMatni(vaqt: Long): String =
    SimpleDateFormat("HH:mm", Locale.US).format(Date(vaqt))

private fun toliqVaqt(vaqt: Long): String =
    SimpleDateFormat("dd.MM HH:mm", Locale.US).format(Date(vaqt))
