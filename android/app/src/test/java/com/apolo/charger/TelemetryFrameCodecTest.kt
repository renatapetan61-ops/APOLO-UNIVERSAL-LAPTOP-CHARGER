package com.apolo.charger

import org.junit.Assert.*
import org.junit.Test

class TelemetryFrameCodecTest {
    @Test fun decodesValidFrame() {
        val frame = TelemetryFrameCodec.decode(makeFrame())
        assertNotNull(frame)
        assertEquals(7, frame!!.sequence)
        assertEquals(51_200L, frame.packVoltageMillivolts)
        assertEquals(1_250, frame.packCurrentMilliamps)
        assertEquals(2_500, frame.temperatureCentiCelsius.toInt())
        assertEquals(78, frame.stateOfChargePercent)
    }
    @Test fun rejectsWrongLength() { assertNull(TelemetryFrameCodec.decode(ByteArray(19))) }
    @Test fun rejectsCorruptedCrc() {
        val bytes = makeFrame(); bytes[7] = (bytes[7].toInt() xor 1).toByte()
        assertNull(TelemetryFrameCodec.decode(bytes))
    }
    @Test fun rejectsUnsupportedVersion() {
        val bytes = makeFrame(); bytes[2] = 2; writeCrc(bytes)
        assertNull(TelemetryFrameCodec.decode(bytes))
    }
    @Test fun rejectsOutOfRangeSoc() {
        val bytes = makeFrame(); bytes[15] = 101; writeCrc(bytes)
        assertNull(TelemetryFrameCodec.decode(bytes))
    }
    private fun makeFrame(): ByteArray {
        val b = ByteArray(20)
        b[0] = 0x41; b[1] = 0x50; b[2] = 1
        putU16(b, 3, 7); putU32(b, 5, 51_200); putU32(b, 9, 1_250)
        putU16(b, 13, 2_500); b[15] = 78; putU16(b, 16, 0); writeCrc(b)
        return b
    }
    private fun putU16(b: ByteArray, o: Int, v: Int) {
        b[o] = (v ushr 8).toByte(); b[o + 1] = v.toByte()
    }
    private fun putU32(b: ByteArray, o: Int, v: Int) {
        b[o] = (v ushr 24).toByte(); b[o + 1] = (v ushr 16).toByte()
        b[o + 2] = (v ushr 8).toByte(); b[o + 3] = v.toByte()
    }
    private fun writeCrc(b: ByteArray) { putU16(b, 18, TelemetryFrameCodec.crc16Ccitt(b, 0, 18)) }
}
