package com.apolo.charger

import org.junit.Assert.*
import org.junit.Test

class DcPolaritySensorCoreTest {
    private val calibration = PolarityCalibration(1.0, 30.0, true)
    private val core = DcPolaritySensorCore(calibration)

    @Test fun noHardwareReadingNeverConfirmsPolarity() {
        val result = core.assess(null, true)
        assertEquals(DcPolarityState.NO_MEASUREMENT, result.state)
        assertFalse(result.polarityConfirmed)
    }

    @Test fun softwareOnlyReadingIsRejected() {
        val result = core.assess(PolarityMeasurement(19.0, 10, false), true)
        assertEquals(DcPolarityState.UNTRUSTED_SOURCE, result.state)
        assertFalse(result.polarityConfirmed)
    }

    @Test fun positiveAndNegativeHardwareSamplesAreClassified() {
        val positive = core.assess(PolarityMeasurement(19.0, 10, true), true)
        val negative = core.assess(PolarityMeasurement(-19.0, 10, true), true)
        assertEquals(DcPolarityState.POSITIVE_CENTER, positive.state)
        assertEquals(DcPolarityState.NEGATIVE_CENTER, negative.state)
        assertTrue(positive.polarityConfirmed)
        assertTrue(negative.polarityConfirmed)
    }

    @Test fun missingEngineeringApprovalBlocksConfirmation() {
        val result = core.assess(PolarityMeasurement(19.0, 10, true), false)
        assertFalse(result.polarityConfirmed)
    }
}
