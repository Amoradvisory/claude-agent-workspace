package com.pilotecours.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.pilotecours.app.ui.components.*
import com.pilotecours.app.ui.theme.*

@Composable
fun AvantEntrerScreen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit,
    onNavigate: (String) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize().background(DarkBackground)) {
        TopBar(title = "Avant d'entrer", fontScale = fontScale, onBackClick = onBack)

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            item { Section("POSTURE", fontScale) }
            item {
                Card {
                    Phrase("Calme — Lent — Stable", fontScale, AccentBlue)
                    Phrase("Voix posée — Regard large", fontScale, AccentBlue)
                    Phrase("Peu de gestes", fontScale, AccentBlue)
                }
            }

            item { Section("NE PAS", fontScale) }
            item {
                Card {
                    Phrase("Parler sur le bruit", fontScale, UrgenceRed)
                    Phrase("Se justifier / Se vexer", fontScale, UrgenceRed)
                    Phrase("Trop expliquer / Menacer", fontScale, UrgenceRed)
                }
            }

            item { Section("RAPPELS", fontScale) }
            item {
                Card {
                    Phrase("Ils testent le cadre, pas ma valeur", fontScale)
                    Phrase("Je corrige tôt et brièvement", fontScale)
                    Phrase("Je n'ai pas besoin d'impressionner", fontScale)
                    Phrase("Je dois être clair", fontScale)
                }
            }
        }
    }
}
