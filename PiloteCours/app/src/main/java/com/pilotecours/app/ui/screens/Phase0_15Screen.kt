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
fun Phase0_15Screen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit,
    onNavigate: (String) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize().background(DarkBackground)) {
        TopBar(title = "0 – 15 min", fontScale = fontScale, onBackClick = onBack)

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            item { Section("ENTRÉE", fontScale) }
            item {
                Card {
                    Phrase("Bonjour. Installez-vous. On commence.", fontScale)
                    Phrase("Je commence quand j'ai tout le monde.", fontScale)
                }
            }

            item { Section("PRÉSENTATION", fontScale) }
            item {
                Card {
                    Phrase("Je suis votre nouveau professeur pour les cours commerciaux.", fontScale)
                    Phrase("Aujourd'hui : faire connaissance, voir le fonctionnement, commencer à travailler.", fontScale)
                }
            }

            item { Section("CADRE", fontScale) }
            item {
                Card {
                    Phrase("Respect, écoute, pas de moqueries, tout le monde essaie.", fontScale, AccentBlue)
                    Phrase("Je ne vous demande pas d'être parfaits. Je vous demande de jouer le jeu.", fontScale, AccentBlue)
                }
            }

            item { Section("LANCEMENT", fontScale) }
            item {
                Card {
                    Phrase("Chacun dit son prénom + une chose qu'il sait bien faire.", fontScale)
                    Phrase("Pas forcément à l'école. Une phrase. On va vite.", fontScale)
                }
            }

            item { Section("SI « JE SAIS RIEN FAIRE »", fontScale) }
            item {
                Card {
                    Phrase("Impossible. Donne une chose simple.", fontScale, AccentOrange)
                    Phrase("Aider, parler, bricoler, convaincre, écouter, organiser…", fontScale, AccentOrange)
                }
            }

            item { Section("TRANSITION", fontScale) }
            item {
                Card {
                    Phrase("Très bien. Je vais vous expliquer comment le cours va fonctionner.", fontScale, AccentGreen)
                }
            }
        }
    }
}
