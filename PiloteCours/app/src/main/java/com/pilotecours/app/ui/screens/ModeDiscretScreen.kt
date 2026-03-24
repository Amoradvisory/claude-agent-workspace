package com.pilotecours.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pilotecours.app.ui.components.TopBar
import com.pilotecours.app.ui.theme.*

@Composable
fun ModeDiscretScreen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize().background(DarkBackground)
    ) {
        TopBar(title = "Discret", fontScale = fontScale, onBackClick = onBack)

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(32.dp),
            verticalArrangement = Arrangement.spacedBy(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(Modifier.height(16.dp))

            // 3 mots posture
            Word("Calme", fontScale, TextPrimary)
            Word("Lent", fontScale, TextPrimary)
            Word("Regard large", fontScale, TextPrimary)

            // Séparateur visuel
            Spacer(Modifier.height(8.dp))

            // Recadrages essentiels
            Word("On écoute", fontScale, AccentOrange)
            Word("On reprend", fontScale, AccentOrange)
            Word("À la fin", fontScale, AccentOrange)

            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
private fun Word(text: String, fontScale: Float, color: androidx.compose.ui.graphics.Color) {
    Text(
        text = text,
        fontSize = (28 * fontScale).sp,
        fontWeight = FontWeight.Bold,
        color = color,
        textAlign = TextAlign.Center
    )
}
