package com.apolo.charger

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ApoloVirtualChipRuntimeTest {
    @Test fun runtimeExecutesFourIndependentSoftwareControllers() {
        val statuses = ApoloVirtualChipRuntime().execute(
            listOf(VirtualObservation("battery_status", "Charging", ObservationOrigin.HOST_OS, 10L, "test-host"))
        )
        assertEquals(4, statuses.size)
        assertEquals(
            setOf("APOLO-BMS-IC", "APOLO-CHARGE-IC", "APOLO-SAFETY-IC", "APOLO-USB-PD-IC"),
            statuses.map { it.id }.toSet()
        )
        assertTrue(statuses.all { it.state == "EXECUTED" })
    }

    @Test fun testFixtureIsNotCountedAsRealObservation() {
        val observation = VirtualObservation("battery_voltage", "12", ObservationOrigin.TEST_FIXTURE, 10L, "unit-test")
        val bms = ApoloBmsIc().execute(listOf(observation))
        assertEquals(0, bms.processedObservations)
    }
}
