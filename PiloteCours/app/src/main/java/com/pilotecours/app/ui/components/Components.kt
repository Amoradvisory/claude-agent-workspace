package com.pilotecours.app.ui.components

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.pilotecours.app.ui.theme.*

// Phrase unique — grosse, lisible
@Composable
fun Phrase(text: String, fontScale: Float = 1f, color: Color = TextPrimary) {
    Text(
        text = text,
        fontSize = (19 * fontScale).sp,
        lineHeight = (27 * fontScale).sp,
        fontWeight = FontWeight.Medium,
        color = color,
        modifier = Modifier.fillMaxWidth()
    )
}

// Séparateur de section — juste un mot en couleur
@Composable
fun Section(title: String, fontScale: Float = 1f) {
    Text(
        text = title.uppercase(),
        fontSize = (13 * fontScale).sp,
        fontWeight = FontWeight.Bold,
        color = AccentBlue,
        letterSpacing = 2.sp,
        modifier = Modifier.padding(top = 16.dp, bottom = 4.dp)
    )
}

// Carte de contenu — fond sombre, coins arrondis, grosse zone tactile
@Composable
fun Card(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = DarkCard)
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            content = content
        )
    }
}

// Gros bouton recadrage — cliquable, appui long = plein écran
@OptIn(ExperimentalFoundationApi::class)
@Composable
fun BigPhraseButton(
    phrase: String,
    fontScale: Float = 1f,
    onLongPress: () -> Unit = {}
) {
    androidx.compose.material3.Card(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(
                onClick = { onLongPress() },
                onLongClick = onLongPress
            ),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = DarkCard)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 22.dp, horizontal = 20.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = phrase,
                fontSize = (22 * fontScale).sp,
                lineHeight = (30 * fontScale).sp,
                fontWeight = FontWeight.SemiBold,
                color = TextPrimary,
                textAlign = TextAlign.Center
            )
        }
    }
}

// Plein écran noir avec phrase géante
@Composable
fun FullScreenPhrase(phrase: String, onDismiss: () -> Unit) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black)
                .clickable { onDismiss() },
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = phrase,
                color = Color.White,
                fontSize = 42.sp,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                lineHeight = 54.sp,
                modifier = Modifier.padding(32.dp)
            )
        }
    }
}

// Barre du bas — 2 boutons seulement : Accueil + Urgence
@Composable
fun BottomBar(
    onHomeClick: () -> Unit,
    onUrgenceClick: () -> Unit
) {
    Surface(
        color = DarkSurface,
        tonalElevation = 4.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Accueil
            FilledTonalButton(
                onClick = onHomeClick,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.filledTonalButtonColors(containerColor = DarkCard)
            ) {
                Icon(Icons.Default.Home, contentDescription = null, tint = AccentBlue, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(8.dp))
                Text("Accueil", fontSize = 15.sp, color = TextPrimary, fontWeight = FontWeight.Medium)
            }

            // Urgence
            Button(
                onClick = onUrgenceClick,
                modifier = Modifier
                    .weight(1f)
                    .height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = UrgenceRed)
            ) {
                Icon(Icons.Default.Warning, contentDescription = null, tint = Color.White, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(8.dp))
                Text("Urgence", fontSize = 15.sp, color = Color.White, fontWeight = FontWeight.Bold)
            }
        }
    }
}

// Barre du haut — juste retour + titre, rien d'autre
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TopBar(
    title: String,
    fontScale: Float = 1f,
    onBackClick: () -> Unit = {}
) {
    TopAppBar(
        title = {
            Text(
                text = title,
                fontSize = (18 * fontScale).sp,
                fontWeight = FontWeight.Bold,
                color = TextPrimary,
                maxLines = 1
            )
        },
        navigationIcon = {
            IconButton(onClick = onBackClick) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, "Retour", tint = TextPrimary)
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(containerColor = DarkBackground)
    )
}
