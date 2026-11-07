package com.apolo.charger

/** Read-only telemetry decoder. It never controls any power hardware. */
data class TelemetryFrame(
    val sequence: Int,
    val packVoltageMillivolts: Long,
    val packCurrentMilliamps: Int,
    val temperatureCentiCelsius: Short,
    val stateOfChargePercent: Int,
    val statusFlags: Int
)

object TelemetryFrameCodec {
    const val FRAME_SIZE = 20
    private const val PROTOCOL_VERSION = 1
    fun decode(bytes: ByteArray): TelemetryFrame? {
        if (bytes.size != FRAME_SIZE) return null
        if (bytes[0] != 0x41.toByte() || bytes[1] != 0x50.toByte()) return null
        if (u8(bytes[2]) != PROTOCOL_VERSION) return null
        if (crc16Ccitt(bytes, 0, 18) != readU16(bytes, 18)) return null
        val sequence = readU16(bytes, 3)
        val voltage = readU32(bytes, 5)
        val current = readI32(bytes, 9)
        val temperature = readU16(bytes, 13).toShort()
        val soc = u8(bytes[15])
        val flags = readU16(bytes, 16)
        if (voltage > 100_000L || current !in -200_000..200_000) return null
        if (temperature.toInt() !in -4_000..12_500 || soc !in 0..100) return null
        return TelemetryFrame(sequence, voltage, current, temperature, soc, flags)
    }

    fun crc16Ccitt(bytes: ByteArray, offset: Int = 0, length: Int = bytes.size): Int {
        require(offset >= 0 && length >= 0 && offset + length <= bytes.size)
        var crc = 0xFFFF
        for (index in offset until offset + length) {
            crc = crc xor (u8(bytes[index]) shl 8)
            repeat(8) {
                crc = if ((crc and 0x8000) != 0) ((crc shl 1) xor 0x1021) and 0xFFFF
                else (crc shl 1) and 0xFFFF
            }
        }
        return crc
    }

    private fun u8(value: Byte) = value.toInt() and 0xFF
    private fun readU16(data: ByteArray, offset: Int) =
        (u8(data[offset]) shl 8) or u8(data[offset + 1])
    private fun readU32(data: ByteArray, offset: Int): Long =
        (u8(data[offset]).toLong() shl 24) or (u8(data[offset + 1]).toLong() shl 16) or
            (u8(data[offset + 2]).toLong() shl 8) or u8(data[offset + 3]).toLong()
    private fun readI32(data: ByteArray, offset: Int): Int =
        (u8(data[offset]) shl 24) or (u8(data[offset + 1]) shl 16) or
            (u8(data[offset + 2]) shl 8) or u8(data[offset + 3])
}
