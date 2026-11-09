package com.apolo.charger

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ApoloObservationContractTest {
    @Test fun acceptsHostOsObservationWithProvenance() {
        val record = ApoloObservationContract.parse("APOLO1\tcpu_load\t12.5\tHOST_OS\t/proc/stat\t1731170000000")
        assertEquals("cpu_load", record?.name)
        assertEquals("HOST_OS", record?.origin)
    }

    @Test fun rejectsTestFixtureAsLiveSensorEvidence() {
        assertNull(ApoloObservationContract.parse("APOLO1\tcpu_load\t12.5\tTEST_FIXTURE\tunit-test\t1731170000000"))
    }

    @Test fun rejectsMissingTimestamp() {
        assertNull(ApoloObservationContract.parse("APOLO1\tcpu_load\t12.5\tHOST_OS\t/proc/stat\t0"))
    }
}
