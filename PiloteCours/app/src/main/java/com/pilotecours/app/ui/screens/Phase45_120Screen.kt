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
fun Phase45_120Screen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit,
    onNavigate: (String) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize().background(DarkBackground)) {
        TopBar(title = "45 – 120 min", fontScale = fontScale, onBackClick = onBack)

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            item { Section("INTRO", fontScale) }
            item {
                Card {
                    Phrase("Avant de comprendre un client, il faut se comprendre soi-même.", fontScale)
                    Phrase("On va travailler : se présenter, écouter, argumenter, vendre.", fontScale)
                }
            }

            item { Section("QUESTIONS", fontScale) }
            item {
                Card {
                    Phrase("Qu'est-ce qu'un bon vendeur ?", fontScale, AccentBlue)
                    Phrase("Qu'est-ce qui donne envie d'écouter quelqu'un ?", fontScale, AccentBlue)
                    Phrase("Qu'est-ce qui agace un client ?", fontScale, AccentBlue)
                    Phrase("Qu'est-ce qu'un vendeur sérieux ?", fontScale, AccentBlue)
                }
            }

            item { Section("SILENCE", fontScale) }
            item {
                Card {
                    Phrase("Juste un mot. Un exemple suffit.", fontScale, AccentOrange)
                    Phrase("Je commence, puis vous continuez.", fontScale, AccentOrange)
                }
            }

            item { Section("BRUIT", fontScale) }
            item {
                Card {
                    Phrase("On revient ensemble.", fontScale, UrgenceRed)
                    Phrase("J'ai besoin de votre attention.", fontScale, UrgenceRed)
                }
            }

            item { Section("TEST", fontScale) }
            item {
                Card {
                    Phrase("On en parle à la fin.", fontScale, AccentOrange)
                    Phrase("Tu reformules correctement.", fontScale, AccentOrange)
                    Phrase("Merci. On avance.", fontScale, AccentGreen)
                }
            }
        }
    }
}
