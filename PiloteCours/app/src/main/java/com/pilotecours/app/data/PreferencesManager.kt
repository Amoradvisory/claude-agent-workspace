package com.pilotecours.app.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "pilotecours_prefs")

class PreferencesManager(private val context: Context) {

    companion object {
        private val FONT_SCALE = intPreferencesKey("font_scale")
        private val LAST_SCREEN = stringPreferencesKey("last_screen")
        private val FAVORITES = stringSetPreferencesKey("favorites")
    }

    val fontScale: Flow<Int> = context.dataStore.data.map { it[FONT_SCALE] ?: 0 }
    val lastScreen: Flow<String> = context.dataStore.data.map { it[LAST_SCREEN] ?: "" }
    val favorites: Flow<Set<String>> = context.dataStore.data.map { it[FAVORITES] ?: emptySet() }

    suspend fun setFontScale(scale: Int) {
        context.dataStore.edit { it[FONT_SCALE] = scale }
    }

    suspend fun setLastScreen(route: String) {
        context.dataStore.edit { it[LAST_SCREEN] = route }
    }

    suspend fun toggleFavorite(route: String) {
        context.dataStore.edit { prefs ->
            val current = prefs[FAVORITES] ?: emptySet()
            prefs[FAVORITES] = if (route in current) current - route else current + route
        }
    }
}
