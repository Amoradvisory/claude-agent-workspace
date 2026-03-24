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
fun FinSeanceScreen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit,
    onNavigate: (String) -> Unit = {}
) {
    Column(modifier = Modifier.fillMaxSize().background(DarkBackground)) {
        TopBar(title = "Fin", fontScale = fontScale, onBackClick = onBack)

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            item {
                Card {
                    Phrase("Je n'attends pas la perfection.", fontScale)
                }
            }
            item {
                Card {
                    Phrase("Être présents, respectueux, capables d'essayer.", fontScale, AccentBlue)
                }
            }
            item {
                Card {
                    Phrase("Si vous jouez le jeu, on avancera bien.", fontScale, AccentGreen)
                }
            }
            item {
                Card {
                    Phrase("Merci.", fontScale)
                }
            }
            item {
                Card {
                    Phrase("La prochaine fois, on travaille directement.", fontScale, TextSecondary)
                }
            }
        }
    }
}
