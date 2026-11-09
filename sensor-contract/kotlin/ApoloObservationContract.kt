package com.apolo.charger.contract

data class ApoloSensorRecord(
    val name: String,
    val value: String,
    val origin: String,
    val source: String,
    val timestampMs: Long
)

object ApoloObservationContract {
    fun parse(line: String): ApoloSensorRecord? {
        val fields = line.trimEnd('\r', '\n').split('\t')
        if (fields.size != 6 || fields[0] != "APOLO1") return null
        val (version, name, value, origin, source, timestamp) = fields
        if (version != "APOLO1" || name.isBlank() || value.isBlank()) return null
        if (origin !in setOf("HOST_OS", "PHYSICAL_INTERFACE")) return null
        if (source.isBlank()) return null
        val epoch = timestamp.toLongOrNull()?.takeIf { it > 0 } ?: return null
        return ApoloSensorRecord(name, value, origin, source, epoch)
    }
}
