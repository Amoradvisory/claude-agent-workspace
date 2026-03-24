package com.pilotecours.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.pilotecours.app.data.PreferencesManager
import com.pilotecours.app.navigation.Screen
import com.pilotecours.app.ui.components.BottomBar
import com.pilotecours.app.ui.screens.*
import com.pilotecours.app.ui.theme.DarkBackground
import com.pilotecours.app.ui.theme.PiloteCoursTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val prefsManager = PreferencesManager(this)

        setContent {
            val fontScaleLevel by prefsManager.fontScale.collectAsState(initial = 0)
            val lastScreen by prefsManager.lastScreen.collectAsState(initial = "")
            val favorites by prefsManager.favorites.collectAsState(initial = emptySet())
            val scope = rememberCoroutineScope()

            val fontScale = when (fontScaleLevel) {
                0 -> 1f
                1 -> 1.3f
                else -> 1.6f
            }

            val navController = rememberNavController()

            fun navigateTo(route: String) {
                if (route != Screen.Home.route) {
                    scope.launch { prefsManager.setLastScreen(route) }
                }
                navController.navigate(route) {
                    launchSingleTop = true
                }
            }

            fun goHome() {
                navController.navigate(Screen.Home.route) {
                    popUpTo(Screen.Home.route) { inclusive = true }
                }
            }

            fun cycleFontScale() {
                scope.launch { prefsManager.setFontScale((fontScaleLevel + 1) % 3) }
            }

            PiloteCoursTheme {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(DarkBackground)
                ) {
                    NavHost(
                        navController = navController,
                        startDestination = Screen.Home.route,
                        modifier = Modifier.weight(1f)
                    ) {
                        composable(Screen.Home.route) {
                            HomeScreen(
                                fontScale = fontScale,
                                lastScreen = lastScreen,
                                favorites = favorites,
                                onNavigate = ::navigateTo
                            )
                        }
                        composable(Screen.AvantEntrer.route) {
                            AvantEntrerScreen(
                                fontScale = fontScale,
                                isFavorite = Screen.AvantEntrer.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.AvantEntrer.route) } },
                                onNavigate = ::navigateTo
                            )
                        }
                        composable(Screen.Phase0_15.route) {
                            Phase0_15Screen(
                                fontScale = fontScale,
                                isFavorite = Screen.Phase0_15.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.Phase0_15.route) } },
                                onNavigate = ::navigateTo
                            )
                        }
                        composable(Screen.Phase15_45.route) {
                            Phase15_45Screen(
                                fontScale = fontScale,
                                isFavorite = Screen.Phase15_45.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.Phase15_45.route) } },
                                onNavigate = ::navigateTo
                            )
                        }
                        composable(Screen.Phase45_120.route) {
                            Phase45_120Screen(
                                fontScale = fontScale,
                                isFavorite = Screen.Phase45_120.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.Phase45_120.route) } },
                                onNavigate = ::navigateTo
                            )
                        }
                        composable(Screen.Recadrages.route) {
                            RecadragesScreen(
                                fontScale = fontScale,
                                isFavorite = Screen.Recadrages.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.Recadrages.route) } }
                            )
                        }
                        composable(Screen.ModeDiscret.route) {
                            ModeDiscretScreen(
                                fontScale = fontScale,
                                isFavorite = Screen.ModeDiscret.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.ModeDiscret.route) } }
                            )
                        }
                        composable(Screen.FinSeance.route) {
                            FinSeanceScreen(
                                fontScale = fontScale,
                                isFavorite = Screen.FinSeance.route in favorites,
                                onBack = { navController.popBackStack() },
                                onFavoriteToggle = { scope.launch { prefsManager.toggleFavorite(Screen.FinSeance.route) } },
                                onNavigate = ::navigateTo
                            )
                        }
                    }

                    BottomBar(
                        onHomeClick = ::goHome,
                        onUrgenceClick = { navigateTo(Screen.Recadrages.route) }
                    )
                }
            }
        }
    }
}
