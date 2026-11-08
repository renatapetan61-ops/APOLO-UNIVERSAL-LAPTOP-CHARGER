package com.apolo.charger

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import kotlin.concurrent.thread

/**
 * Exports the Windows bootstrap installer to user-selected shared storage.
 * Android cannot silently execute PowerShell on a USB-connected Windows host.
 */
@Composable
fun AmisWindowsInstallerTransferPanel() {
    val context = LocalContext.current
    var status by remember { mutableStateOf("Prepare o instalador para transferi-lo ao notebook pelo cabo USB.") }
    var busy by remember { mutableStateOf(false) }
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
                    val text = bytes.toString(Charsets.UTF_8)
                    require(text.startsWith("#requires -Version")) { "O arquivo recebido não parece ser um script PowerShell válido." }
                    context.contentResolver.openOutputStream(uri, "wt")?.use { it.write(bytes) }
                        ?: error("Não foi possível gravar o arquivo escolhido.")
                    val digest = MessageDigest.getInstance("SHA-256").digest(bytes)
                        .joinToString("") { "%02x".format(it) }
                    "Instalador salvo. SHA-256: $digest"
                }
                android.os.Handler(android.os.Looper.getMainLooper()).post {
                    status = result.fold(
                        onSuccess = { "$it\nAgora copie install_amis_windows.ps1 para o notebook usando a transferência de arquivos USB (MTP)." },
                        onFailure = { "Falha ao preparar o instalador: ${it.message}" }
                    )
                    busy = false
                }
            }
        }
    }

    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Instalação do agente AMIS no Windows", style = MaterialTheme.typography.titleMedium)
            Text("O aplicativo baixa o instalador oficial e salva uma cópia escolhida por você. Depois, copie o arquivo para o notebook pelo modo Transferência de arquivos (MTP).")
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
            Text(status, style = MaterialTheme.typography.bodySmall)
            Text(
                "No Windows, clique com o botão direito no arquivo e escolha Executar com PowerShell, ou abra PowerShell na pasta e execute .\\install_amis_windows.ps1. O script pede que você digite INSTALAR antes de fazer alterações. Ele baixa o pacote do GitHub por HTTPS, instala o agente no perfil do usuário e inicia o serviço local. Não é possível o Android executar um .ps1 diretamente no Windows apenas por conectar o cabo USB.",
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

private const val INSTALLER_URL =
    "https://raw.githubusercontent.com/renatapetan61-ops/APOLO-UNIVERSAL-LAPTOP-CHARGER/main/host-agent/install_amis_windows.ps1"
