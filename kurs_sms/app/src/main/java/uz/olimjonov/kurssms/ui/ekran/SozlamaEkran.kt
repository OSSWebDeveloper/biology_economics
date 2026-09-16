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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import uz.olimjonov.kurssms.ui.AsosiyViewModel

private val ORALIQLAR = listOf(15, 30, 60, 120, 360)

@Composable
fun SozlamaEkran(
    holat: AsosiyViewModel.Holat,
    onUlan: (String, String) -> Unit,
    onUzil: () -> Unit,
    onSaqla: (String, Int, Int, Int) -> Unit,
    onTekshir: () -> Unit,
    onSimYubor: () -> Unit,
    onSimRuxsat: () -> Unit,
    onOrqaga: () -> Unit,
) {
    var manzil by remember { mutableStateOf(holat.manzil) }
    var kod by remember { mutableStateOf("") }
    var oraliq by remember { mutableStateOf(holat.oraliq) }
    var tanaffus by remember { mutableStateOf(holat.tanaffus.toString()) }
    var birMartada by remember { mutableStateOf(holat.birMartada.toString()) }

    fun saqla() = onSaqla(
        manzil,
        oraliq,
        tanaffus.toIntOrNull() ?: 4,
        birMartada.toIntOrNull() ?: 10,
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Sozlamalar") },
                navigationIcon = {
                    IconButton(onClick = { saqla(); onOrqaga() }) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Orqaga")
                    }
                },
            )
        }
    ) { chekka ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(chekka)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Spacer(Modifier.height(4.dp))

            // ------------------------------------------------------ sayt
            Text("Sayt", style = MaterialTheme.typography.titleMedium)

            OutlinedTextField(
                value = manzil,
                onValueChange = { manzil = it },
                label = { Text("Sayt manzili") },
                placeholder = { Text("https://kurs.example.uz") },
                supportingText = { Text("Bir tarmoqda sinash uchun: http://192.168.1.5:8000") },
                singleLine = true,
                enabled = !holat.ulangan,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                modifier = Modifier.fillMaxWidth(),
            )

            // --------------------------------------------------- ulanish
            if (holat.ulangan) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    ),
                ) {
                    Column(Modifier.padding(14.dp)) {
                        Text(
                            "Saytga ulangan",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold,
                        )
                        if (holat.saytNomi.isNotBlank()) {
                            Text(holat.saytNomi, style = MaterialTheme.typography.bodyMedium)
                        }
                        if (holat.qurilmaNomi.isNotBlank()) {
                            Text(
                                "Saytdagi nomi: ${holat.qurilmaNomi}",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                        Spacer(Modifier.height(10.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(
                                onClick = { saqla(); onTekshir() },
                                enabled = !holat.ishlamoqda,
                            ) { Text("Aloqani tekshirish") }
                            OutlinedButton(onClick = onUzil) { Text("Uzish") }
                        }
                    }
                }
            } else {
                Text("Saytga ulanish", style = MaterialTheme.typography.titleMedium)
                Text(
                    "Saytda \"Xabarnoma\" bo'limiga kirib \"Ulanish kodini olish\" ni bosing " +
                        "va chiqqan 12 raqamni shu yerga kiriting.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                OutlinedTextField(
                    value = kod,
                    onValueChange = { yangi -> kod = yangi.filter { it.isDigit() }.take(12) },
                    label = { Text("Ulanish kodi (12 raqam)") },
                    placeholder = { Text("049125081866") },
                    supportingText = { Text(kodKorinishi(kod)) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = { onUlan(manzil, kod) },
                    enabled = !holat.ishlamoqda && kod.length == 12 && manzil.isNotBlank(),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    if (holat.ishlamoqda) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onPrimary,
                        )
                        Spacer(Modifier.size(8.dp))
                    }
                    Text("Ulanish")
                }
            }

            if (holat.xabar.isNotBlank()) {
                Text(
                    text = holat.xabar,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (holat.yaxshi == false) MaterialTheme.colorScheme.error
                    else MaterialTheme.colorScheme.primary,
                )
            }

            HorizontalDivider()

            // -------------------------------------------------- SIM lar
            Text("SIM kartalar", style = MaterialTheme.typography.titleMedium)
            if (holat.simlar.isEmpty()) {
                Text(
                    "SIM ro'yxatini ko'rsatish uchun telefon holati ruxsati kerak. " +
                        "Ruxsat berilmasa, telefonning standart SIM kartasi ishlatiladi.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                OutlinedButton(onClick = onSimRuxsat) { Text("Ruxsat berish") }
            } else {
                for (sim in holat.simlar) {
                    Text(
                        "• ${sim.nomi}" + if (sim.raqam.isNotBlank()) "  ${sim.raqam}" else "",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                Text(
                    "Qaysi SIM dan yuborilishini SAYT belgilaydi (Xabarlar bo'limida).",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                if (holat.ulangan) {
                    OutlinedButton(onClick = onSimYubor, enabled = !holat.ishlamoqda) {
                        Text("SIM ro'yxatini saytga yuborish")
                    }
                }
            }

            HorizontalDivider()

            // ------------------------------------------------- tekshiruv
            Text("Tekshirish oralig'i", style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ORALIQLAR.forEach { daqiqa ->
                    FilterChip(
                        selected = oraliq == daqiqa,
                        onClick = { oraliq = daqiqa },
                        label = {
                            Text(if (daqiqa < 60) "$daqiqa daq" else "${daqiqa / 60} soat")
                        },
                    )
                }
            }
            Text(
                "Android eng kami 15 daqiqaga ruxsat beradi.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            HorizontalDivider()

            Text("Jo'natish tezligi", style = MaterialTheme.typography.titleMedium)

            OutlinedTextField(
                value = birMartada,
                onValueChange = { yangi -> birMartada = yangi.filter { it.isDigit() }.take(2) },
                label = { Text("Bir tekshiruvda eng ko'pi (ta)") },
                supportingText = {
                    Text(
                        "Android 30 daqiqada 30 tadan ko'p SMS ga ruxsat so'raydi. " +
                            "10 ta - xavfsiz chegara."
                    )
                },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
            )

            OutlinedTextField(
                value = tanaffus,
                onValueChange = { yangi -> tanaffus = yangi.filter { it.isDigit() }.take(2) },
                label = { Text("SMS lar orasidagi tanaffus (soniya)") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(Modifier.height(4.dp))

            Button(
                onClick = { saqla(); onOrqaga() },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Saqlash")
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    "Kurs SMS  v${holat.versiya}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Spacer(Modifier.height(24.dp))
        }
    }
}

/** "049125081866" -> "0491 2508 1866" */
private fun kodKorinishi(kod: String): String {
    if (kod.isEmpty()) return "Saytdagi 12 xonalik kod"
    return kod.chunked(4).joinToString(" ")
}
