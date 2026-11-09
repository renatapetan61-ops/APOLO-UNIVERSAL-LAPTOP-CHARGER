package com.apolo.charger

import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
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
    val system: String,
    val found: Int,
    val corrected: Int,
    val notCorrected: Int,
    val findings: List<String>,
    val correctedItems: List<String>,
    val recommendations: List<String>,
    val mode: String,
    val windowsRepairAvailable: Boolean
)

private fun parseApoloReport(json: JSONObject): RepairReport {
    val summary = json.getJSONObject("summary")
    fun strings(arrayName: String): List<String> {
        val array = json.getJSONArray(arrayName)
        return (0 until array.length()).map { index ->
            val item = array.getJSONObject(index)
            if (item.has("title")) "${item.getString("title")}: ${item.optString("detail")}" else item.toString()
        }
    }
    val host = json.optJSONObject("host") ?: JSONObject()
    val policy = json.optJSONObject("repair_policy") ?: JSONObject()
    val actions = policy.optJSONArray("available_actions")
    val repairAvailable = (0 until (actions?.length() ?: 0)).any {
        actions?.optString(it) == "WINDOWS_SFC_REPAIR"
    }
    return RepairReport(
        system = host.optString("system", "Unknown"),
        found = summary.optInt("found"),
        corrected = summary.optInt("corrected"),
        notCorrected = summary.optInt("not_corrected"),
        findings = strings("findings"),
        correctedItems = strings("corrected"),
        recommendations = (0 until json.getJSONArray("recommendations").length())
            .map { json.getJSONArray("recommendations").getString(it) },
        mode = policy.optString("mode", "UNKNOWN"),
        windowsRepairAvailable = repairAvailable
    )
}

private fun requestApolo(path: String, method: String = "GET", body: String? = null,
                         timeoutMs: Int = 45000): JSONObject {
    val connection = (URL("http://127.0.0.1:8765$path").openConnection() as HttpURLConnection)
    connection.requestMethod = method
    connection.connectTimeout = 5000
    connection.readTimeout = timeoutMs
    connection.setRequestProperty("Accept", "application/json")
    connection.setRequestProperty("Cache-Control", "no-store")
    if (body != null) {
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
    }
    try {
        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val response = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
        if (code !in 200..299) error("Agente respondeu HTTP $code: $response")
        return JSONObject(response)
    } finally {
        connection.disconnect()
    }
}

@Composable
fun RepairScreen() {
    var busy by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Conecte o notebook e inicie o agente APOLO autorizado.") }
    var report by remember { mutableStateOf<RepairReport?>(null) }
    var repairPrompt by remember { mutableStateOf(false) }
    var repairMessage by remember { mutableStateOf<String?>(null) }

    fun run() {
        busy = true
        report = null
        status = "Executando os quatro controladores virtuais e consultando telemetria do notebook..."
        Thread {
            val result = runCatching { parseApoloReport(requestApolo("/v1/diagnostics/run", timeoutMs = 90000)) }
            Handler(Looper.getMainLooper()).post {
                result.onSuccess {
                    report = it
                    status = "Diagnóstico concluído. O relatório será exibido neste aplicativo."
                }.onFailure {
                    status = "Não foi possível executar o diagnóstico: ${it.message}. Verifique o agente e a ponte ADB USB."
                }
                busy = false
            }
        }.start()
    }

    fun executeRepair() {
        repairPrompt = false
        busy = true
        repairMessage = null
        status = "Executando a verificação e, se necessário, o reparo autorizado do Windows. Não desligue o notebook."
        Thread {
            val result = runCatching {
                val action = requestApolo(
                    "/v1/repairs/windows/system-file-check", "POST",
                    """{"confirm":true}""", timeoutMs = 1_200_000
                )
                val fresh = parseApoloReport(requestApolo("/v1/diagnostics/run", timeoutMs = 90000))
                val actionStatus = action.optString("status", "UNRESOLVED")
                val corrected = action.optInt("corrected_count", 0)
                val actionMessage = action.optString("message", "Resultado da ação não informado.")
                val actionWasNeeded = actionStatus != "NOT_NEEDED"
                val findings = fresh.findings + if (actionWasNeeded) listOf(
                    "Integridade dos arquivos protegidos do Windows: $actionMessage"
                ) else emptyList()
                val correctedItems = fresh.correctedItems + if (corrected > 0) listOf(
                    "Arquivos protegidos do Windows: reparo confirmado por verificação posterior."
                ) else emptyList()
                val unresolved = if (actionWasNeeded && corrected == 0) listOf(
                    "Reparo dos arquivos protegidos do Windows: $actionMessage"
                ) else emptyList()
                fresh.copy(
                    found = fresh.found + if (actionWasNeeded) 1 else 0,
                    corrected = fresh.corrected + corrected,
                    notCorrected = fresh.notCorrected + unresolved.size,
                    findings = findings,
                    correctedItems = correctedItems,
                    recommendations = fresh.recommendations + unresolved,
                    mode = "CONSENTED_REPAIR_AND_POSTCHECK"
                ) to actionMessage
            }
            Handler(Looper.getMainLooper()).post {
                result.onSuccess { (updated, message) ->
                    report = updated
                    repairMessage = message
                    status = "Ação concluída. O relatório atualizado está no aplicativo."
                }.onFailure {
                    repairMessage = "Reparo não executado ou não verificado: ${it.message}"
                    status = repairMessage.orEmpty()
                }
                busy = false
            }
        }.start()
    }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Consertar erros do notebook", style = MaterialTheme.typography.headlineMedium)
        Text("O APOLO consulta telemetria real disponibilizada pelo sistema operacional. Os quatro chips são controladores virtuais de software.")
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("APOLO-BMS IC • APOLO-CHARGE IC • APOLO-SAFETY IC • APOLO-USB-PD IC")
                Text("Sensores virtuais processam observações identificadas. Temperatura, tensão e corrente só são exibidas quando uma fonte do sistema as fornece.")
            }
        }
        Button(onClick = { run() }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
            if (busy) CircularProgressIndicator() else Text("Ativar chips e diagnosticar notebook")
        }
        Text(status, style = MaterialTheme.typography.bodyMedium)
        Text("As verificações incluem CPU, memória, GPU, armazenamento, drivers e identificação eletrônica da placa-mãe, conforme os dados expostos pelo sistema operacional.")
        Text("Correções que alteram o sistema exigem confirmação. Nesta versão, o reparo disponível é limitado à verificação dos arquivos protegidos do Windows com SFC, quando o agente está elevado como Administrador.")
        repairMessage?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
    }

    report?.let { value ->
        AlertDialog(
            onDismissRequest = { if (!busy) report = null },
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
                    if (value.correctedItems.isEmpty()) Text("Nenhum erro foi alterado ou confirmado como corrigido.")
                    value.correctedItems.forEach { Text("• $it") }
                    Text("Como evitar novos problemas", style = MaterialTheme.typography.titleSmall)
                    value.recommendations.forEach { Text("• $it") }
                    Text("Modo: ${value.mode}", style = MaterialTheme.typography.labelSmall)
                }
            },
            confirmButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(androidx.compose.ui.unit.dp(8))) {
                    TextButton(onClick = { report = null }, enabled = !busy) { Text("Fechar") }
                    if (value.windowsRepairAvailable && value.system == "Windows") {
                        Button(onClick = { repairPrompt = true }, enabled = !busy) {
                            Text("Reparar Windows")
                        }
                    }
                }
            }
        )
    }

    if (repairPrompt) {
        AlertDialog(
            onDismissRequest = { repairPrompt = false },
            title = { Text("Autorizar reparo do Windows?") },
            text = { Text("O APOLO executará SFC /verifyonly e, se encontrar corrupção, SFC /scannow. Isso pode alterar arquivos protegidos do Windows, exigir privilégios de Administrador e levar vários minutos. Depois será executada uma nova verificação. Deseja continuar?") },
            confirmButton = { Button(onClick = { executeRepair() }) { Text("Autorizar e continuar") } },
            dismissButton = { TextButton(onClick = { repairPrompt = false }) { Text("Cancelar") } }
        )
    }
}
