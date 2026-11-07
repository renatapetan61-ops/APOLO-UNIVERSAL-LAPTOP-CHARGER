package com.apolo.charger

/**
 * Compatibility data recorded for the first target laptop.
 * Values are transcribed from the user's previously reported adapter label,
 * not independently verified against the laptop's DC input specification.
 */
data class ApoloLaptopProfile(
    val model: String,
    val nominalInputVoltageV: Double,
    val adapterRatedCurrentA: Double,
    val connectorDescription: String?,
    val polarityDescription: String?,
    val source: String,
    val electricallyVerified: Boolean
) {
    val adapterRatedPowerW: Double
        get() = nominalInputVoltageV * adapterRatedCurrentA

    fun canAuthorizePowerOutput(): Boolean =
        electricallyVerified &&
            connectorDescription?.isNotBlank() == true &&
            polarityDescription?.isNotBlank() == true
}

object ApoloLaptopProfiles {
    /**
     * Initial reference only: user-reported original adapter rating.
     * Connector, polarity, input tolerance and identification requirements
     * remain unknown, so this profile must not authorize an output.
     */
    val POSITIVO_UNIQUE_TV_S2065 = ApoloLaptopProfile(
        model = "Positivo Unique TV S2065",
        nominalInputVoltageV = 19.0,
        adapterRatedCurrentA = 3.42,
        connectorDescription = null,
        polarityDescription = null,
        source = "Etiqueta do carregador original informada pelo usuário",
        electricallyVerified = false
    )
}
