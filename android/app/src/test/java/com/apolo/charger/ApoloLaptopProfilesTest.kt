package com.apolo.charger

import org.junit.Assert.*
import org.junit.Test

class ApoloLaptopProfilesTest {
    @Test fun positivoProfileUsesReportedAdapterRating() {
        val profile = ApoloLaptopProfiles.POSITIVO_UNIQUE_TV_S2065
        assertEquals("Positivo Unique TV S2065", profile.model)
        assertEquals(19.0, profile.nominalInputVoltageV, 0.001)
        assertEquals(3.42, profile.adapterRatedCurrentA, 0.001)
        assertEquals(64.98, profile.adapterRatedPowerW, 0.01)
    }

    @Test fun unknownConnectorAndPolarityNeverAuthorizeOutput() {
        val profile = ApoloLaptopProfiles.POSITIVO_UNIQUE_TV_S2065
        assertNull(profile.connectorDescription)
        assertNull(profile.polarityDescription)
        assertFalse(profile.canAuthorizePowerOutput())
    }

    @Test fun profileRequiresExplicitElectricalVerification() {
        val incomplete = ApoloLaptopProfiles.POSITIVO_UNIQUE_TV_S2065.copy(
            connectorDescription = "conector identificado",
            polarityDescription = "polaridade identificada",
            electricallyVerified = false
        )
        assertFalse(incomplete.canAuthorizePowerOutput())
    }
}
