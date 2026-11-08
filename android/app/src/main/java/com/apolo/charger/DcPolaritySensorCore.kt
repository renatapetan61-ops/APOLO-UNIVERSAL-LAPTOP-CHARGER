package com.apolo.charger

/**
 * Software analyzer for the future APOLO Power Module polarity measurement channel.
 *
 * This class does not generate an electrical measurement. A real, isolated ADC
 * front-end must provide center-to-sleeve voltage samples. Until then the state
 * is NO_MEASUREMENT and polarityConfirmed is always false.
 */
data class PolarityCalibration(
    val minimumDetectableVoltageV: Double,
    val maximumMeasurementVoltageV: Double,
    val validatedByEngineering: Boolean
)

data class PolarityMeasurement(
    /** Voltage measured as center contact minus outer sleeve. */
    val centerToSleeveVoltageV: Double,
    val sampleAgeMs: Long,
    /** True only for samples delivered by the isolated Power Module ADC. */
    val fromVerifiedHardwareAdc: Boolean
)

enum class DcPolarityState {
    NO_MEASUREMENT,
    UNTRUSTED_SOURCE,
    STALE_MEASUREMENT,
    INVALID_MEASUREMENT,
    POSITIVE_CENTER,
    NEGATIVE_CENTER,
    AMBIGUOUS
}

data class DcPolarityAssessment(
    val state: DcPolarityState,
    val polarityConfirmed: Boolean = false,
    val measuredVoltageV: Double? = null,
    val explanation: String
)

class DcPolaritySensorCore(
    private val calibration: PolarityCalibration?,
    private val maximumSampleAgeMs: Long = 1_000
) {
    fun assess(measurement: PolarityMeasurement?, engineeringApproved: Boolean): DcPolarityAssessment {
        if (measurement == null) return result(DcPolarityState.NO_MEASUREMENT, "Aguardando leitura do ADC isolado do Power Module.")
        if (!measurement.fromVerifiedHardwareAdc) {
            return result(DcPolarityState.UNTRUSTED_SOURCE, "A leitura não veio de um ADC físico autenticado do módulo.")
        }
        if (measurement.sampleAgeMs < 0 || measurement.sampleAgeMs > maximumSampleAgeMs) {
            return result(DcPolarityState.STALE_MEASUREMENT, "Amostra elétrica vencida.")
        }
        val c = calibration
        if (c == null || !engineeringApproved || !c.validatedByEngineering ||
            !c.minimumDetectableVoltageV.isFinite() || !c.maximumMeasurementVoltageV.isFinite() ||
            c.minimumDetectableVoltageV <= 0.0 ||
            c.maximumMeasurementVoltageV <= c.minimumDetectableVoltageV) {
            return result(DcPolarityState.INVALID_MEASUREMENT, "Calibração elétrica não validada; polaridade não pode ser confirmada.")
        }
        val v = measurement.centerToSleeveVoltageV
        if (!v.isFinite() || kotlin.math.abs(v) > c.maximumMeasurementVoltageV) {
            return result(DcPolarityState.INVALID_MEASUREMENT, "Leitura fora da faixa segura de medição.")
        }
        if (kotlin.math.abs(v) < c.minimumDetectableVoltageV) {
            return result(DcPolarityState.AMBIGUOUS, "Tensão insuficiente para distinguir a polaridade.")
        }
        return if (v > 0.0) {
            DcPolarityAssessment(DcPolarityState.POSITIVE_CENTER, true, v, "Centro positivo em relação à luva externa.")
        } else {
            DcPolarityAssessment(DcPolarityState.NEGATIVE_CENTER, true, v, "Centro negativo em relação à luva externa.")
        }
    }

    private fun result(state: DcPolarityState, explanation: String) =
        DcPolarityAssessment(state = state, explanation = explanation)
}
