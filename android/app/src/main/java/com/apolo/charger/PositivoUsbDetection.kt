package com.apolo.charger

/**
 * USB identity is only a peripheral fingerprint. It is NOT proof that a
 * connected peripheral is the laptop chassis, nor that its DC jack polarity
 * is correct. The S2065 fingerprint is intentionally empty until verified
 * identifiers and a laptop-side companion protocol exist.
 */
data class UsbFingerprint(val vendorId: Int, val productId: Int)

enum class LaptopUsbMatch {
    TARGET_CONFIRMED,
    OTHER_USB_DEVICE,
    NO_USB_DEVICE,
    TARGET_FINGERPRINT_NOT_CONFIGURED
}

object PositivoUsbIdentity {
    // Do not guess VID/PID values. Populate only from a verified S2065 device
    // enumeration and a companion protocol that proves the host identity.
    val approvedFingerprints: Set<UsbFingerprint> = emptySet()

    fun classify(devices: List<UsbFingerprint>): LaptopUsbMatch {
        if (devices.isEmpty()) return LaptopUsbMatch.NO_USB_DEVICE
        if (approvedFingerprints.isEmpty()) return LaptopUsbMatch.TARGET_FINGERPRINT_NOT_CONFIGURED
        return if (devices.any { it in approvedFingerprints }) {
            LaptopUsbMatch.TARGET_CONFIRMED
        } else {
            LaptopUsbMatch.OTHER_USB_DEVICE
        }
    }
}
