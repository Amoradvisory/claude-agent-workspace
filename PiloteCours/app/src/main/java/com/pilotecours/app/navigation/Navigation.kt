package com.pilotecours.app.navigation

enum class Screen(val route: String, val title: String, val emoji: String) {
    Home("home", "Pilote Cours", ""),
    AvantEntrer("avant_entrer", "Avant d'entrer", "\uD83C\uDFAF"),
    Phase0_15("phase_0_15", "0 – 15 min", "\uD83D\uDE80"),
    Phase15_45("phase_15_45", "15 – 45 min", "\uD83D\uDCDA"),
    Phase45_120("phase_45_120", "45 – 120 min", "\u26A1"),
    Recadrages("recadrages", "Recadrages", "\uD83D\uDEE1\uFE0F"),
    ModeDiscret("mode_discret", "Mode discret", "\uD83E\uDD2B"),
    FinSeance("fin_seance", "Fin de séance", "\u2705");

    companion object {
        fun fromRoute(route: String): Screen? = entries.find { it.route == route }

        // Écrans dans l'ordre séquentiel du cours
        val sequentialScreens = listOf(AvantEntrer, Phase0_15, Phase15_45, Phase45_120, FinSeance)

        fun nextScreen(current: Screen): Screen? {
            val idx = sequentialScreens.indexOf(current)
            return if (idx in 0 until sequentialScreens.lastIndex) sequentialScreens[idx + 1] else null
        }

        fun prevScreen(current: Screen): Screen? {
            val idx = sequentialScreens.indexOf(current)
            return if (idx > 0) sequentialScreens[idx - 1] else null
        }
    }
}
