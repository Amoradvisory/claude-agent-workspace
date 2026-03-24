package com.pilotecours.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.pilotecours.app.navigation.Screen
import com.pilotecours.app.ui.theme.*

@Composable
fun HomeScreen(
    fontScale: Float,
    lastScreen: String,
    favorites: Set<String>,
    onNavigate: (String) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Spacer(Modifier.height(4.dp))

        // Titre minimal
        Text(
            text = "PILOTE",
            fontSize = (24 * fontScale).sp,
            fontWeight = FontWeight.Bold,
            color = TextSecondary,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth()
        )

        // Reprendre — gros et visible
        if (lastScreen.isNotEmpty()) {
            val screen = Screen.fromRoute(lastScreen)
            if (screen != null && screen != Screen.Home) {
                Card(
                    onClick = { onNavigate(lastScreen) },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = AccentBlue)
                ) {
                    Row(
                        modifier = Modifier
                            .padding(vertical = 18.dp, horizontal = 20.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.PlayArrow, null, tint = Color.White, modifier = Modifier.size(28.dp))
                        Spacer(Modifier.width(12.dp))
                        Text(
                            screen.title,
                            fontSize = (20 * fontScale).sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                    }
                }
            }
        }

        // Boutons — très gros, simple texte
        HomeButton("Avant d'entrer", DarkCard, TextPrimary, fontScale) { onNavigate(Screen.AvantEntrer.route) }
        HomeButton("0 – 15 min", DarkCard, TextPrimary, fontScale) { onNavigate(Screen.Phase0_15.route) }
        HomeButton("15 – 45 min", DarkCard, TextPrimary, fontScale) { onNavigate(Screen.Phase15_45.route) }
        HomeButton("45 – 120 min", DarkCard, TextPrimary, fontScale) { onNavigate(Screen.Phase45_120.route) }
        HomeButton("Recadrages", UrgenceRed.copy(alpha = 0.25f), UrgenceRed, fontScale) { onNavigate(Screen.Recadrages.route) }
        HomeButton("Discret", DarkCard, AccentOrange, fontScale) { onNavigate(Screen.ModeDiscret.route) }
        HomeButton("Fin", DarkCard, TextSecondary, fontScale) { onNavigate(Screen.FinSeance.route) }

        Spacer(Modifier.height(4.dp))
    }
}

@Composable
private fun HomeButton(
    label: String,
    bgColor: Color,
    textColor: Color,
    fontScale: Float,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = bgColor)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 22.dp, horizontal = 20.dp),
            contentAlignment = Alignment.CenterStart
        ) {
            Text(
                text = label,
                fontSize = (21 * fontScale).sp,
                fontWeight = FontWeight.SemiBold,
                color = textColor
            )
        }
    }
}
