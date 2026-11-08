package com.apolo.charger

import org.junit.Assert.assertEquals
import org.junit.Test

class PositivoUsbIdentityTest {
    @Test fun noUsbDevicesIsNotLaptop() {
        assertEquals(LaptopUsbMatch.NO_USB_DEVICE, PositivoUsbIdentity.classify(emptyList()))
    }

    @Test fun unknownPeripheralNeverClaimsToBePositivo() {
        assertEquals(
            LaptopUsbMatch.TARGET_FINGERPRINT_NOT_CONFIGURED,
            PositivoUsbIdentity.classify(listOf(UsbFingerprint(0x1234, 0x5678)))
        )
    }

    @Test fun targetIdentityCannotBeClaimedWithoutVerifiedFingerprint() {
        assertEquals(emptySet<UsbFingerprint>(), PositivoUsbIdentity.approvedFingerprints)
    }
}
