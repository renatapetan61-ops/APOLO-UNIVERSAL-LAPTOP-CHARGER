package com.apolo.charger

import org.junit.Assert.*
import org.junit.Test

class UsbLaptopAuthenticationTest {
    private val key = ByteArray(32) { (it + 1).toByte() }
    private val nonce = ByteArray(32) { (it + 3).toByte() }

    @Test fun missingProvisioningDoesNotAuthenticate() {
        val result = UsbLaptopAuthentication.verify(null, nonce, null)
        assertEquals(LaptopAuthenticationState.NOT_CONFIGURED, result.state)
    }

    @Test fun validS2065ProofAuthenticates() {
        val proof = UsbLaptopAuthentication.createProof(
            UsbLaptopAuthentication.POSITIVO_S2065_MODEL_ID, nonce, key
        )
        val result = UsbLaptopAuthentication.verify(proof, nonce, key)
        assertEquals(LaptopAuthenticationState.AUTHENTICATED, result.state)
    }

    @Test fun wrongModelNonceOrKeyIsRejected() {
        val wrongModel = UsbLaptopAuthentication.createProof("other.model", nonce, key)
        assertEquals(
            LaptopAuthenticationState.REJECTED,
            UsbLaptopAuthentication.verify(wrongModel, nonce, key).state
        )
        val valid = UsbLaptopAuthentication.createProof(
            UsbLaptopAuthentication.POSITIVO_S2065_MODEL_ID, nonce, key
        )
        assertEquals(
            LaptopAuthenticationState.REJECTED,
            UsbLaptopAuthentication.verify(valid, ByteArray(32), key).state
        )
        assertEquals(
            LaptopAuthenticationState.REJECTED,
            UsbLaptopAuthentication.verify(valid, nonce, ByteArray(32) { 9 }).state
        )
    }
}
