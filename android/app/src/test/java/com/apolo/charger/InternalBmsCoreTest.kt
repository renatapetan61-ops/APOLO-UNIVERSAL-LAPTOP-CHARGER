package com.apolo.charger

import org.junit.Assert.*
import org.junit.Test

class InternalBmsCoreTest {
    private val profile = ApoloBatteryProfile("test-profile", "LiFePO4", 4, 100, 20_000, true)
    private val limits = ApoloBmsLimits(2.5, 3.65, 45.0, 60.0, 30.0, 2_000)
    private val core = InternalBmsCore(profile, limits)

    @Test fun missingTelemetryIsInvalidAndNeverPermitsOutput() {
        val result = core.assess(null, 10_000)
        assertEquals(ApoloBmsState.DATA_INVALID, result.state)
        assertFalse(result.powerOutputPermitted)
    }

    @Test fun validTelemetryProducesNormalStatus() {
        val sample = ApoloSensorSnapshot(listOf(3.2, 3.21, 3.19, 3.2), 25.0, 2.0, 10_000)
        assertEquals(ApoloBmsState.NORMAL, core.assess(sample, 10_100).state)
    }

    @Test fun staleTelemetryFailsClosed() {
        val sample = ApoloSensorSnapshot(listOf(3.2, 3.2, 3.2, 3.2), 25.0, 0.0, 1_000)
        assertEquals(ApoloBmsState.DATA_INVALID, core.assess(sample, 10_000).state)
    }

    @Test fun criticalCellVoltageIsReported() {
        val sample = ApoloSensorSnapshot(listOf(2.4, 3.2, 3.2, 3.2), 25.0, 0.0, 10_000)
        assertEquals(ApoloBmsState.CRITICAL, core.assess(sample, 10_000).state)
    }

    @Test fun unvalidatedProfileCannotBeUsed() {
        val unvalidated = InternalBmsCore(profile.copy(limitsValidatedByEngineering = false), limits)
        assertEquals(ApoloBmsState.UNCONFIGURED, unvalidated.assess(null, 0).state)
    }

    @Test fun socEstimatorAccountsForDischarge() {
        val soc = ApoloSocEstimator.integrate(80.0, 1_000.0, 3_600_000, 10_000.0)
        assertEquals(70.0, soc!!, 0.0001)
    }
}
