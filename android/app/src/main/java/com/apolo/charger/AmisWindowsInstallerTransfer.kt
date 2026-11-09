package com.apolo.charger

import android.net.Uri
import android.os.Handler
import android.os.Looper
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import kotlin.concurrent.thread

/**
 * Exports the Windows bootstrap script and sends a one-time user approval
 * to the Windows installer over an ADB-authorized USB reverse tunnel.
 */
@Composable
fun AmisWindowsInstallerTransferPanel() {
    val context = LocalContext.current
    var status by remember { mutableStateOf("Prepare o instalador e transfira-o para o notebook.") }
    var busy by remember { mutableStateOf(false) }
    var approvalCode by remember { mutableStateOf("") }

    val createDocument = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/x-powershell")
    ) { uri: Uri? ->
        if (uri == null) {
            status = "Exportação cancelada."
            busy = false
        } else {
            thread(name = "amis-installer-download") {
                val result = runCatching {
                    val connection = (URL(INSTALLER_URL).openConnection() as HttpURLConnection).apply {
                        requestMethod = "GET"
                        connectTimeout = 12000
                        readTimeout = 20000
                        setRequestProperty("Accept", "text/plain")
                    }
                    val bytes = try {
                        if (connection.responseCode != 200) error("GitHub retornou HTTP ${connection.responseCode}")
                        connection.inputStream.use { it.readBytes() }
                    } finally {
                        connection.disconnect()
                    }
                    require(bytes.isNotEmpty() && bytes.size < 256 * 1024) { "Tamanho inesperado do instalador." }
                    require(bytes.toString(Charsets.UTF_8).startsWith("#requires -Version")) {
                        "O arquivo recebido não parece ser um script PowerShell válido."
                    }
                    context.contentResolver.openOutputStream(uri, "wt")?.use { it.write(bytes) }
                        ?: error("Não foi possível gravar o arquivo escolhido.")
                    val digest = MessageDigest.getInstance("SHA-256").digest(bytes)
                        .joinToString("") { "%02x".format(it) }
                    "Instalador salvo. SHA-256: $digest"
                }
                Handler(Looper.getMainLooper()).post {
                    status = result.fold(
                        onSuccess = { "$it\nCopie o arquivo para o notebook via USB/MTP. Depois execute-o no PowerShell." },
                        onFailure = { "Falha ao preparar o instalador: ${it.message}" }
                    )
                    busy = false
                }
            }
        }
    }

    fun authorizeInstallation() {
        val code = approvalCode.filter { it.isDigit() }
        if (code.length != 6) {
            status = "Informe o código temporário de seis dígitos exibido no PowerShell do notebook."
            return
        }
        busy = true
        thread(name = "amis-install-approval") {
            val result = runCatching {
                val connection = (URL(APPROVAL_URL).openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 5000
                    readTimeout = 8000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    setRequestProperty("Cache-Control", "no-store")
                }
                val payload = """{"code":"$code"}""".toByteArray(Charsets.UTF_8)
                try {
                    connection.outputStream.use { it.write(payload) }
                    val responseCode = connection.responseCode
                    val response = (if (responseCode in 200..299) connection.inputStream else connection.errorStream)
                        ?.bufferedReader()?.use { it.readText() }.orEmpty()
                    if (responseCode != 200) error("Windows recusou a autorização (HTTP $responseCode). Confira o código e a conexão USB.")
                    response
                } finally {
                    connection.disconnect()
                }
            }
            Handler(Looper.getMainLooper()).post {
                status = result.fold(
                    onSuccess = {
                        approvalCode = ""
                        "Autorização enviada com sucesso. O instalador Windows pode continuar e preparar o Host Agent."
                    },
                    onFailure = {
                        "Não foi possível autorizar: ${it.message}. Confirme que o PowerShell está aguardando, que a Depuração USB foi autorizada e que o ADB reverse está ativo."
                    }
                )
                busy = false
            }
        }
    }

    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Instalação do agente AMIS no Windows", style = MaterialTheme.typography.titleMedium)
            Text("1. Prepare o instalador. 2. Copie-o para o notebook por USB/MTP. 3. Execute-o no PowerShell. 4. Digite abaixo o código temporário que aparecerá na janela do Windows.")
            Button(
                onClick = {
                    busy = true
                    createDocument.launch("install_amis_windows.ps1")
                },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(if (busy) "Preparando..." else "Preparar instalador Windows")
            }
            OutlinedTextField(
                value = approvalCode,
                onValueChange = { approvalCode = it.filter(Char::isDigit).take(6) },
                label = { Text("Código de autorização do Windows") },
                supportingText = { Text("Código temporário de seis dígitos exibido pelo instalador.") },
                singleLine = true,
                enabled = !busy,
                modifier = Modifier.fillMaxWidth()
            )
            Button(
                onClick = { authorizeInstallation() },
                enabled = !busy && approvalCode.length == 6,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(if (busy) "Aguardando resposta..." else "Confirmar e autorizar instalação no notebook")
            }
            Text(status, style = MaterialTheme.typography.bodySmall)
            Text(
                "O botão envia uma autorização de uso único pela ponte ADB USB. Ele não concede privilégios administrativos nem inicia o PowerShell remotamente: o usuário precisa executar o instalador no Windows e aceitar a autorização de depuração USB do Android. O instalador expira após cinco minutos se não receber a confirmação.",
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

private const val INSTALLER_URL =
    "https://raw.githubusercontent.com/renatapetan61-ops/APOLO-UNIVERSAL-LAPTOP-CHARGER/fix/runtime-bms-amis-ci/host-agent/install_amis_windows.ps1"
private const val APPROVAL_URL = "http://127.0.0.1:8766/v1/install/approve"
