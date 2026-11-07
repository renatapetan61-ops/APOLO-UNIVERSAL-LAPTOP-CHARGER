package com.apolo.charger

/**
 * Software representation of the APOLO Power Module.
 * It models energy/output requests but deliberately exposes no hardware driver.
 */
data class ApoloPowerModuleProfile(
    val moduleName: String,
    val nominalEnergyWh: Int,
    val maximumOutputWatts: Int,
    val batteryChemistry: String,
    val engineeringDesignApproved: Boolean
)

enum class ApoloOutputType { USB_C_PD, DC_BARREL, USB_A_DATA }

data class ApoloOutputRequest(
    val type: ApoloOutputType,
    val requestedVoltageV: Double,
    val requestedPowerW: Double,
    val laptopProfileVerified: Boolean
)

data class ApoloOutputDecision(
    val acceptedForHardware: Boolean,
    val reason: String
)

class ApoloPowerModuleCore(private val profile: ApoloPowerModuleProfile?) {
    fun describe(): String {
        if (profile == null) return "Módulo não configurado"
        return "${profile.moduleName}: ${profile.nominalEnergyWh} Wh; limite conceitual ${profile.maximumOutputWatts} W; ${profile.batteryChemistry}"
    }

    /**
     * Until independently validated hardware and safety certification exist,
     * every real output request is denied. This is intentional fail-closed behavior.
     */
    fun evaluateOutputRequest(request: ApoloOutputRequest): ApoloOutputDecision {
        if (profile == null || !profile.engineeringDesignApproved) {
            return ApoloOutputDecision(false, "Projeto elétrico não aprovado; saída bloqueada")
        }
        if (request.type == ApoloOutputType.USB_A_DATA) {
            return ApoloOutputDecision(false, "USB-A não é uma saída de alimentação para carregar o notebook")
        }
        if (!request.laptopProfileVerified) {
            return ApoloOutputDecision(false, "Perfil elétrico do notebook não foi verificado")
        }
        if (!request.requestedVoltageV.isFinite() || request.requestedVoltageV <= 0 ||
            !request.requestedPowerW.isFinite() || request.requestedPowerW <= 0 ||
            request.requestedPowerW > profile.maximumOutputWatts) {
            return ApoloOutputDecision(false, "Solicitação fora do perfil configurado")
        }
        return ApoloOutputDecision(false, "Saída física indisponível nesta versão de software")
    }
}
