package com.apolo.charger

import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * Cryptographic verifier for a future laptop-side APOLO companion.
 * Transport over a generic phone-to-laptop USB cable is platform-dependent
 * and is deliberately not faked by this protocol-only component.
 */
data class LaptopChallenge(val nonce: ByteArray)
data class LaptopProof(val modelId: String, val nonce: ByteArray, val hmacSha256: ByteArray)

enum class LaptopAuthenticationState { NOT_CONFIGURED, AUTHENTICATED, REJECTED }

data class LaptopAuthenticationResult(
    val state: LaptopAuthenticationState,
    val modelId: String? = null,
    val explanation: String
)

object UsbLaptopAuthentication {
    const val POSITIVO_S2065_MODEL_ID = "positivo.unique-tv.s2065"

    fun verify(
        proof: LaptopProof?,
        expectedNonce: ByteArray?,
        provisionedKey: ByteArray?
    ): LaptopAuthenticationResult {
        if (proof == null || expectedNonce == null || provisionedKey == null || provisionedKey.size < 32) {
            return LaptopAuthenticationResult(
                LaptopAuthenticationState.NOT_CONFIGURED,
                explanation = "Agente APOLO e chave de identidade ainda não foram provisionados."
            )
        }
        if (proof.modelId != POSITIVO_S2065_MODEL_ID ||
            !MessageDigest.isEqual(proof.nonce, expectedNonce)) {
            return LaptopAuthenticationResult(
                LaptopAuthenticationState.REJECTED,
                explanation = "Modelo ou desafio criptográfico não corresponde."
            )
        }
        val expectedMac = hmac(provisionedKey, proof.modelId, proof.nonce)
        if (!MessageDigest.isEqual(expectedMac, proof.hmacSha256)) {
            return LaptopAuthenticationResult(
                LaptopAuthenticationState.REJECTED,
                explanation = "Prova criptográfica inválida."
            )
        }
        return LaptopAuthenticationResult(
            LaptopAuthenticationState.AUTHENTICATED,
            proof.modelId,
            "Agente APOLO autenticado; isso não valida conector, tensão ou polaridade."
        )
    }

    /** Used by the companion agent and deterministic tests. Keep keys out of source control. */
    fun createProof(modelId: String, nonce: ByteArray, provisionedKey: ByteArray): LaptopProof =
        LaptopProof(modelId, nonce.copyOf(), hmac(provisionedKey, modelId, nonce))

    private fun hmac(key: ByteArray, modelId: String, nonce: ByteArray): ByteArray {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key, "HmacSHA256"))
        mac.update(modelId.toByteArray(Charsets.UTF_8))
        mac.update(0.toByte())
        mac.update(nonce)
        return mac.doFinal()
    }
}
