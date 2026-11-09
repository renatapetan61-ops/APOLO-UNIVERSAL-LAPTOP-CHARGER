package com.apolo.charger

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
        val name = fields[1]
        val value = fields[2]
        val origin = fields[3]
        val source = fields[4]
        val timestamp = fields[5].toLongOrNull()?.takeIf { it > 0 } ?: return null
        if (name.isBlank() || value.isBlank() || source.isBlank()) return null
        if (origin !in setOf("HOST_OS", "PHYSICAL_INTERFACE")) return null
        return ApoloSensorRecord(name, value, origin, source, timestamp)
    }
}
