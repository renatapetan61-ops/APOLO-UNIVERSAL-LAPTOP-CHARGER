package com.apolo.charger

import org.junit.Assert.*
import org.junit.Test

class PowerModuleCoreTest {
    @Test fun outputRemainsLockedWithoutApprovedDesign() {
        val module = ApoloPowerModuleCore(ApoloPowerModuleProfile("APOLO", 1500, 240, "LiFePO4", false))
        val result = module.evaluateOutputRequest(ApoloOutputRequest(ApoloOutputType.USB_C_PD, 20.0, 100.0, true))
        assertFalse(result.acceptedForHardware)
    }

    @Test fun usbAIsNeverAcceptedAsLaptopPowerOutput() {
        val module = ApoloPowerModuleCore(ApoloPowerModuleProfile("APOLO", 1500, 240, "LiFePO4", true))
        val result = module.evaluateOutputRequest(ApoloOutputRequest(ApoloOutputType.USB_A_DATA, 5.0, 2.0, true))
        assertFalse(result.acceptedForHardware)
        assertTrue(result.reason.contains("USB-A"))
    }

    @Test fun unverifiedLaptopProfileIsRejected() {
        val module = ApoloPowerModuleCore(ApoloPowerModuleProfile("APOLO", 1500, 240, "LiFePO4", true))
        val result = module.evaluateOutputRequest(ApoloOutputRequest(ApoloOutputType.DC_BARREL, 19.0, 65.0, false))
        assertFalse(result.acceptedForHardware)
    }
}
