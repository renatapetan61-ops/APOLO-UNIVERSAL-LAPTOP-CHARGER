package com.apolo.charger

import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

private data class RepairReport(
    val found: Int,
    val corrected: Int,
    val notCorrected: Int,
    val findings: List<String>,
    val correctedItems: List<String>,
    val recommendations: List<String>,
    val mode: String
)

@Composable
fun RepairScreen() {
    var busy by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Conecte o notebook e inicie o agente APOLO autorizado.") }
    var report by remember { mutableStateOf<RepairReport?>(null) }

    fun run() {
        busy = true
        report = null
        status = "Executando os quatro controladores virtuais e consultando evidências do notebook..."
        Thread {
            val result = runCatching {
                val connection = (URL("http://127.0.0.1:8765/v1/diagnostics/run").openConnection() as HttpURLConnection)
                connection.requestMethod = "POST"
                connection.connectTimeout = 5000
                connection.readTimeout = 45000
                connection.setRequestProperty("Accept", "application/json")
                connection.setRequestProperty("Cache-Control", "no-store")
                val code = connection.responseCode
                val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                val body = stream.bufferedReader().use { it.readText() }
                connection.disconnect()
                if (code !in 200..299) error("Agente respondeu HTTP $code: $body")
                val json = JSONObject(body)
                val summary = json.getJSONObject("summary")
                val findings = json.getJSONArray("findings")
                val corrected = json.getJSONArray("corrected")
                val recommendations = json.getJSONArray("recommendations")
                fun strings(array: org.json.JSONArray): List<String> =
                    (0 until array.length()).map { index ->
                        val item = array.getJSONObject(index)
                        if (item.has("title")) "${item.getString("title")}: ${item.optString("detail")}" else item.toString()
                    }
                RepairReport(
                    summary.getInt("found"), summary.getInt("corrected"),
                    summary.getInt("not_corrected"), strings(findings), strings(corrected),
                    (0 until recommendations.length()).map { recommendations.getString(it) },
                    json.getJSONObject("repair_policy").getString("mode")
                )
            }
            Handler(Looper.getMainLooper()).post {
                result.onSuccess {
                    report = it
                    status = "Diagnóstico concluído. O relatório será exibido neste aplicativo."
                }.onFailure {
                    status = "Não foi possível executar o diagnóstico: ${it.message}. Verifique a conexão USB/ADB e o agente do notebook."
                }
                busy = false
            }
        }.start()
    }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Consertar erros do notebook", style = MaterialTheme.typography.headlineMedium)
        Text("O APOLO consulta informações reais disponibilizadas pelo sistema operacional do notebook. Os quatro chips são controladores virtuais de software executados no aplicativo/agente.")
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("APOLO-BMS IC • APOLO-CHARGE IC • APOLO-SAFETY IC • APOLO-USB-PD IC")
                Text("Sensores virtuais: recebem dados identificados do sistema operacional. Não conseguem medir sinais elétricos físicos por conta própria.")
            }
        }
        Button(onClick = { run() }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
            if (busy) CircularProgressIndicator() else Text("Ativar chips e diagnosticar notebook")
        }
        Text(status, style = MaterialTheme.typography.bodyMedium)
        Text("Nesta primeira etapa, a execução é somente leitura. Nenhum driver, arquivo, firmware ou configuração será alterado automaticamente. Uma correção só será contabilizada quando houver uma ação segura, autorização e verificação posterior.")
    }

    report?.let { value ->
        AlertDialog(
            onDismissRequest = { report = null },
            title = { Text("APOLO — Relatório final") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Erros encontrados: ${value.found}")
                    Text("Erros corrigidos: ${value.corrected}")
                    Text("Erros não corrigidos: ${value.notCorrected}")
                    Text("Erros encontrados", style = MaterialTheme.typography.titleSmall)
                    if (value.findings.isEmpty()) Text("Nenhum erro foi confirmado pelas verificações disponíveis.")
                    value.findings.forEach { Text("• $it") }
                    Text("Erros corrigidos", style = MaterialTheme.typography.titleSmall)
                    if (value.correctedItems.isEmpty()) Text("Nenhum erro foi alterado nesta versão.")
                    value.correctedItems.forEach { Text("• $it") }
                    Text("Como evitar novos problemas", style = MaterialTheme.typography.titleSmall)
                    value.recommendations.forEach { Text("• $it") }
                    Text("Modo: ${value.mode}", style = MaterialTheme.typography.labelSmall)
                }
            },
            confirmButton = { TextButton(onClick = { report = null }) { Text("Fechar") } }
        )
    }
}
