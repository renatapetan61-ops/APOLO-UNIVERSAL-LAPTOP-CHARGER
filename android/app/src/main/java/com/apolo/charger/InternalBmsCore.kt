package com.apolo.charger

/**
 * APOLO's internal, software-only BMS domain model.
 *
 * This module evaluates supplied telemetry and reports status. It is NOT a
 * battery protection circuit and has no actuator or power-stage interface.
 * Missing, stale, or invalid data always produces a non-operational state.
 */
data class ApoloBatteryProfile(
    val profileId: String,
    val chemistry: String,
    val seriesCellCount: Int,
    val nominalEnergyWh: Int,
    val capacityMah: Int,
    val limitsValidatedByEngineering: Boolean
)

data class ApoloBmsLimits(
    val minimumCellVoltage: Double,
    val maximumCellVoltage: Double,
    val warningTemperatureC: Double,
    val criticalTemperatureC: Double,
    val maximumAbsoluteCurrentA: Double,
    val maximumSampleAgeMs: Long
)

data class ApoloSensorSnapshot(
    val cellVoltages: List<Double>,
    val temperatureC: Double,
    val currentA: Double,
    val receivedAtMs: Long
)

enum class ApoloBmsState { UNCONFIGURED, DATA_INVALID, NORMAL, WARNING, CRITICAL }

data class ApoloBmsAssessment(
    val state: ApoloBmsState,
    val reasons: List<String>,
    val minimumCellVoltage: Double?,
    val maximumCellVoltage: Double?,
    val powerOutputPermitted: Boolean = false
)

class InternalBmsCore(
    private val profile: ApoloBatteryProfile?,
    private val limits: ApoloBmsLimits?
) {
    fun assess(snapshot: ApoloSensorSnapshot?, nowMs: Long): ApoloBmsAssessment {
        if (profile == null || limits == null || !profile.limitsValidatedByEngineering || !limits.limitsValidatedByContract()) {
            return result(ApoloBmsState.UNCONFIGURED, "Perfil e limites de engenharia não validados")
        }
        if (snapshot == null) return result(ApoloBmsState.DATA_INVALID, "Nenhuma telemetria recebida")
        if (profile.seriesCellCount <= 0 || profile.capacityMah <= 0 ||
            profile.nominalEnergyWh <= 0 || profile.chemistry.isBlank()) {
            return result(ApoloBmsState.UNCONFIGURED, "Perfil da bateria incompleto")
        }
        if (snapshot.cellVoltages.size != profile.seriesCellCount ||
            snapshot.cellVoltages.any { !it.isFinite() || it <= 0.0 } ||
            !snapshot.temperatureC.isFinite() || !snapshot.currentA.isFinite() ||
            snapshot.receivedAtMs > nowMs || nowMs - snapshot.receivedAtMs > limits.maximumSampleAgeMs) {
            return result(ApoloBmsState.DATA_INVALID, "Sensores ausentes, inválidos ou telemetria vencida")
        }

        val minCell = snapshot.cellVoltages.minOrNull()
        val maxCell = snapshot.cellVoltages.maxOrNull()
        val reasons = mutableListOf<String>()
        if (minCell!! < limits.minimumCellVoltage || maxCell!! > limits.maximumCellVoltage) {
            reasons += "Tensão de célula fora dos limites configurados"
        }
        if (snapshot.temperatureC >= limits.criticalTemperatureC) {
            reasons += "Temperatura crítica"
        }
        if (kotlin.math.abs(snapshot.currentA) > limits.maximumAbsoluteCurrentA) {
            reasons += "Corrente acima do limite configurado"
        }
        if (reasons.isNotEmpty()) return ApoloBmsAssessment(ApoloBmsState.CRITICAL, reasons, minCell, maxCell)

        if (snapshot.temperatureC >= limits.warningTemperatureC) {
            return ApoloBmsAssessment(
                ApoloBmsState.WARNING,
                listOf("Temperatura em faixa de alerta"),
                minCell,
                maxCell
            )
        }
        return ApoloBmsAssessment(ApoloBmsState.NORMAL, listOf("Telemetria válida"), minCell, maxCell)
    }

    private fun ApoloBmsLimits.limitsValidatedByContract(): Boolean =
        minimumCellVoltage.isFinite() && maximumCellVoltage.isFinite() &&
            minimumCellVoltage > 0 && maximumCellVoltage > minimumCellVoltage &&
            warningTemperatureC.isFinite() && criticalTemperatureC > warningTemperatureC &&
            maximumAbsoluteCurrentA.isFinite() && maximumAbsoluteCurrentA > 0 &&
            maximumSampleAgeMs > 0

    private fun result(state: ApoloBmsState, reason: String) =
        ApoloBmsAssessment(state, listOf(reason), null, null)
}

/** Positive current means discharge. This is an estimate, not a fuel gauge. */
object ApoloSocEstimator {
    fun integrate(
        previousSocPercent: Double,
        currentMilliAmps: Double,
        elapsedMs: Long,
        capacityMilliAmpHours: Double
    ): Double? {
        if (!previousSocPercent.isFinite() || previousSocPercent !in 0.0..100.0 ||
            !currentMilliAmps.isFinite() || elapsedMs < 0 ||
            !capacityMilliAmpHours.isFinite() || capacityMilliAmpHours <= 0.0
        ) return null
        val dischargedMah = currentMilliAmps * (elapsedMs / 3_600_000.0)
        return (previousSocPercent - dischargedMah / capacityMilliAmpHours * 100.0).coerceIn(0.0, 100.0)
    }
}
