package uz.olimjonov.kurssms.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Yashil = Color(0xFF1B6B4A)
private val YashilOch = Color(0xFF7FD1A8)
private val Qizil = Color(0xFFB3261E)
private val QizilOch = Color(0xFFFFB4AB)

private val YorugRanglar = lightColorScheme(
    primary = Yashil,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFCDEFDD),
    onPrimaryContainer = Color(0xFF00210F),
    secondary = Color(0xFF4F6354),
    background = Color(0xFFF6F7F5),
    onBackground = Color(0xFF191C1A),
    surface = Color.White,
    onSurface = Color(0xFF191C1A),
    surfaceVariant = Color(0xFFE4E5E1),
    error = Qizil,
)

private val QorongiRanglar = darkColorScheme(
    primary = YashilOch,
    onPrimary = Color(0xFF00391F),
    primaryContainer = Color(0xFF005230),
    onPrimaryContainer = Color(0xFF9BF6C3),
    secondary = Color(0xFFB6CCBA),
    background = Color(0xFF111412),
    onBackground = Color(0xFFE1E3DF),
    surface = Color(0xFF1A1D1B),
    onSurface = Color(0xFFE1E3DF),
    surfaceVariant = Color(0xFF3F4945),
    error = QizilOch,
)

@Composable
fun KursSmsTheme(qorongi: Boolean = isSystemInDarkTheme(), tarkib: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (qorongi) QorongiRanglar else YorugRanglar,
        content = tarkib,
    )
}
