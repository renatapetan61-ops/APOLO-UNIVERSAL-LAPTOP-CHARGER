package com.apolo.charger

/**
 * APOLO virtual IC runtime.
 *
 * These are executable software controllers, not silicon chips. Sensor adapters
 * accept only observations supplied by the host OS or an explicitly identified
 * test source; they never manufacture physical measurements.
 */
enum class ObservationOrigin { HOST_OS, PHYSICAL_INTERFACE, TEST_FIXTURE, UNKNOWN }

data class VirtualObservation(
    val name: String,
    val value: String?,
    val origin: ObservationOrigin,
    val observedAtEpochMs: Long,
    val source: String
) {
    fun isUsableForDiagnostics(): Boolean =
        value != null && origin != ObservationOrigin.UNKNOWN &&
            origin != ObservationOrigin.TEST_FIXTURE && source.isNotBlank()
}

data class VirtualChipStatus(
    val id: String,
    val state: String,
    val processedObservations: Int,
    val notes: List<String>
)

interface ApoloVirtualIc {
    val id: String
    fun execute(observations: List<VirtualObservation>): VirtualChipStatus
}

class ApoloBmsIc : ApoloVirtualIc {
    override val id = "APOLO-BMS-IC"
    override fun execute(observations: List<VirtualObservation>): VirtualChipStatus {
        val battery = observations.filter {
            it.name.contains("battery", true) || it.name.contains("power_supply", true)
        }
        return VirtualChipStatus(
            id, "EXECUTED", battery.count { it.isUsableForDiagnostics() },
            listOf("Avalia somente telemetria de bateria realmente fornecida pelo host.")
        )
    }
}

class ApoloChargeIc : ApoloVirtualIc {
    override val id = "APOLO-CHARGE-IC"
    override fun execute(observations: List<VirtualObservation>): VirtualChipStatus {
        val power = observations.filter {
            it.name.contains("power", true) || it.name.contains("adapter", true)
        }
        return VirtualChipStatus(
            id, "EXECUTED", power.count { it.isUsableForDiagnostics() },
            listOf("Não controla carregamento nem mede tensão elétrica pelo cabo USB.")
        )
    }
}

class ApoloSafetyIc : ApoloVirtualIc {
    override val id = "APOLO-SAFETY-IC"
    override fun execute(observations: List<VirtualObservation>): VirtualChipStatus {
        val unknown = observations.count { !it.isUsableForDiagnostics() }
        return VirtualChipStatus(
            id, "EXECUTED", observations.size,
            listOf("$unknown observação(ões) sem evidência utilizável; nenhuma ação de risco autorizada.")
        )
    }
}

class ApoloUsbPdIc : ApoloVirtualIc {
    override val id = "APOLO-USB-PD-IC"
    override fun execute(observations: List<VirtualObservation>): VirtualChipStatus {
        val usb = observations.filter { it.name.contains("usb", true) }
        return VirtualChipStatus(
            id, "EXECUTED", usb.count { it.isUsableForDiagnostics() },
            listOf("Analisa informações USB disponibilizadas pelo host; não negocia PD sem controlador USB-C compatível.")
        )
    }
}

class ApoloVirtualSensorEngine {
    fun accept(observations: List<VirtualObservation>): List<VirtualObservation> =
        observations.filter { it.source.isNotBlank() && it.observedAtEpochMs > 0L }
}

class ApoloVirtualChipRuntime {
    private val sensors = ApoloVirtualSensorEngine()
    private val chips: List<ApoloVirtualIc> = listOf(
        ApoloBmsIc(), ApoloChargeIc(), ApoloSafetyIc(), ApoloUsbPdIc()
    )

    fun execute(observations: List<VirtualObservation>): List<VirtualChipStatus> {
        val accepted = sensors.accept(observations)
        return chips.map { it.execute(accepted) }
    }
}
