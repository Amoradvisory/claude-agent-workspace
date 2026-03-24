package com.pilotecours.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.pilotecours.app.ui.components.*
import com.pilotecours.app.ui.theme.*

@Composable
fun RecadragesScreen(
    fontScale: Float,
    isFavorite: Boolean,
    onBack: () -> Unit,
    onFavoriteToggle: () -> Unit
) {
    val phrases = listOf(
        "On écoute.",
        "On reprend.",
        "Un seul parle.",
        "On ne commente pas.",
        "On en parle à la fin.",
        "Merci. On avance.",
        "Reformule.",
        "Les autres écoutent."
    )

    var fullScreenPhrase by remember { mutableStateOf<String?>(null) }

    if (fullScreenPhrase != null) {
        FullScreenPhrase(phrase = fullScreenPhrase!!, onDismiss = { fullScreenPhrase = null })
    }

    Column(modifier = Modifier.fillMaxSize().background(DarkBackground)) {
        TopBar(title = "Recadrages", fontScale = fontScale, onBackClick = onBack)

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            items(phrases) { phrase ->
                BigPhraseButton(
                    phrase = phrase,
                    fontScale = fontScale,
                    onLongPress = { fullScreenPhrase = phrase }
                )
            }
        }
    }
}
