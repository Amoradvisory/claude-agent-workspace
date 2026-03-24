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
fun Phase15_45Screen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit,
    onNavigate: (String) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize().background(DarkBackground)) {
        TopBar(title = "15 – 45 min", fontScale = fontScale, onBackClick = onBack)

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            item { Section("MÉTHODE", fontScale) }
            item {
                Card {
                    Phrase("On ne va pas recopier. On travaille concrètement : parler, observer, mises en situation.", fontScale)
                    Phrase("L'objectif : que ce soit utile. Magasin, stage, job, communication.", fontScale, AccentBlue)
                }
            }

            item { Section("ÉVALUATION", fontScale) }
            item {
                Card {
                    Phrase("Évaluation surtout pratique.", fontScale)
                    Phrase("Participation, implication, communication, progression.", fontScale)
                    Phrase("Le but : vous faire progresser, pas vous piéger.", fontScale, AccentGreen)
                }
            }

            item { Section("VÉRIFICATION", fontScale) }
            item {
                Card {
                    Phrase("Qui peut me redire une règle du cours ?", fontScale, AccentOrange)
                    Phrase("Qui peut me redire comment on sera évalués ?", fontScale, AccentOrange)
                }
            }

            item { Section("RÉFLEXION", fontScale) }
            item {
                Card {
                    Phrase("Chacun réfléchit :", fontScale)
                    Phrase("1. Une force que j'ai", fontScale, AccentBlue)
                    Phrase("2. Une chose à améliorer", fontScale, AccentBlue)
                    Phrase("Qui commence ? Une phrase courte.", fontScale)
                }
            }
        }
    }
}
