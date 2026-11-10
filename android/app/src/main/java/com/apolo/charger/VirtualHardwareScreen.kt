package com.apolo.charger

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import java.net.HttpURLConnection
import java.net.URL

@Composable
fun VirtualHardwareScreen() {
    var response by remember { mutableStateOf("Ainda não consultado. Inicie o Host Agent no notebook e configure a ponte ADB autorizada.") }
    var loading by remember { mutableStateOf(false) }

    Button(
        onClick = {
            loading = true
            Thread {
                val result = runCatching {
                    val connection = URL("http://127.0.0.1:8765/v1/virtual-hardware/snapshot")
                        .openConnection() as HttpURLConnection
                    connection.requestMethod = "GET"
                    connection.connectTimeout = 3000
                    connection.readTimeout = 5000
                    connection.setRequestProperty("Cache-Control", "no-store")
                    val code = connection.responseCode
                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                    val body = stream.bufferedReader().use { it.readText() }
                    connection.disconnect()
                    if (code !in 200..299) error("Host Agent respondeu HTTP $code: $body")
                    body
                }.fold(
                    onSuccess = { it },
                    onFailure = { "Não foi possível obter a placa virtual: ${it.message}" }
                )
                android.os.Handler(android.os.Looper.getMainLooper()).post {
                    response = result
                    loading = false
                }
            }.start()
        },
        enabled = !loading,
        modifier = Modifier.fillMaxWidth()
    ) { Text(if (loading) "Consultando placa..." else "Ler estado da placa virtual no notebook") }

    Text("APOLO Virtual Hardware Board", style = MaterialTheme.typography.headlineMedium)
    Text("Painel de emulação: dispositivos I²C, BMS 16S, Safety, estágio de potência e USB-C PD.")
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Proveniência e segurança", style = MaterialTheme.typography.titleMedium)
            Text("HARDWARE_EMULATION — entradas sintéticas. Nenhum sensor físico foi medido.")
            Text("Saída de potência: permanentemente bloqueada nesta emulação.")
            Text("USB-PD: contratos apenas calculados; não existe negociação elétrica.")
        }
    }
    Card {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Resposta do Host Agent", style = MaterialTheme.typography.titleMedium)
            Text(response, style = MaterialTheme.typography.bodySmall)
        }
    }
}
