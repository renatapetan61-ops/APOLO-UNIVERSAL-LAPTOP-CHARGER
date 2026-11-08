package com.apolo.charger

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.usb.UsbManager
import android.os.Build
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

private data class UsbScanState(
    val devices: List<UsbFingerprint> = emptyList(),
    val descriptions: List<String> = emptyList(),
    val match: LaptopUsbMatch = LaptopUsbMatch.NO_USB_DEVICE,
    val hostApiAvailable: Boolean = false
)

@Composable
fun ConnectionScreen() {
    val context = LocalContext.current
    var scan by remember { mutableStateOf(UsbScanState()) }

    fun refresh() {
        val manager = context.getSystemService(Context.USB_SERVICE) as? UsbManager
        val connected = manager?.deviceList?.values?.toList().orEmpty()
        val fingerprints = connected.map { UsbFingerprint(it.vendorId, it.productId) }
        scan = UsbScanState(
            devices = fingerprints,
            descriptions = connected.map {
                "USB VID %04X / PID %04X — %s".format(it.vendorId, it.productId, it.deviceName)
            },
            match = PositivoUsbIdentity.classify(fingerprints),
            hostApiAvailable = manager != null
        )
    }

    DisposableEffect(context) {
        refresh()
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context?, intent: Intent?) {
                refresh()
            }
        }
        val filter = IntentFilter().apply {
            addAction(UsbManager.ACTION_USB_DEVICE_ATTACHED)
            addAction(UsbManager.ACTION_USB_DEVICE_DETACHED)
        }
        if (Build.VERSION.SDK_INT >= 33) {
            context.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("DEPRECATION")
            context.registerReceiver(receiver, filter)
        }
        onDispose { runCatching { context.unregisterReceiver(receiver) } }
    }

    val laptop = ApoloLaptopProfiles.POSITIVO_UNIQUE_TV_S2065
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Conectividade", style = MaterialTheme.typography.headlineMedium)
        Text("Notebook cadastrado: ${laptop.model}", style = MaterialTheme.typography.titleMedium)
        Text("Referência do adaptador informado: 19 V × 3,42 A = ${"%.2f".format(java.util.Locale.US, laptop.adapterRatedPowerW)} W.")
        Button(onClick = { refresh() }, modifier = Modifier.fillMaxWidth()) {
            Text("Verificar conexão USB agora")
        }
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Resultado da verificação USB", style = MaterialTheme.typography.titleMedium)
                Text(
                    when (scan.match) {
                        LaptopUsbMatch.TARGET_CONFIRMED -> "Identidade USB reconhecida — ainda não valida a polaridade nem autoriza energia."
                        LaptopUsbMatch.OTHER_USB_DEVICE -> "Há dispositivo USB conectado, mas ele não corresponde à identidade cadastrada."
                        LaptopUsbMatch.NO_USB_DEVICE -> "Nenhum periférico USB foi enumerado pelo Android em modo USB Host."
                        LaptopUsbMatch.TARGET_FINGERPRINT_NOT_CONFIGURED -> "Dispositivo USB detectado, mas a identidade USB do Positivo S2065 ainda não foi validada/configurada."
                    }
                )
                if (scan.descriptions.isEmpty()) Text("Nenhum VID/PID disponível.")
                scan.descriptions.forEach { Text(it, style = MaterialTheme.typography.bodySmall) }
            }
        }
        Text("Limitação importante: ao ligar o celular por cabo USB comum ao notebook, normalmente o notebook é o host USB e o celular é o periférico. Nesse cenário, o Android não recebe a identidade do notebook pela API USB Host. A enumeração acima só mostra periféricos que o celular consegue hospedar, por exemplo via OTG.")
        Text("Identificação do Positivo: para confirmar o modelo de verdade, será necessário um agente no notebook que responda a um desafio criptográfico por um canal de dados compatível, ou uma interface APOLO dedicada. Nome Bluetooth, nome USB ou VID/PID isolado não bastam para autenticação.")
        Text("Sensor interno de polaridade APOLO: o aplicativo agora contém um analisador de software que classifica amostras center-to-sleeve recebidas do ADC isolado do Power Module. Sem esse sinal físico, o estado permanece AGUARDANDO MEDIÇÃO e nunca afirma uma polaridade. O cabo USB de dados sozinho não fornece a tensão do jack DC.")
        Text("Identidade autenticada APOLO: o núcleo criptográfico HMAC-SHA256 para o agente do notebook foi criado. Ele só confirma o S2065 quando recebe uma prova válida, um desafio recente e uma chave provisionada. A camada de transporte USB direto ainda depende de suporte do host/Android e do agente instalado no notebook; esta versão não finge que o cabo comum já fornece essa comunicação.")
        Text("Estado de segurança: saída de energia BLOQUEADA. A detecção USB não confirma compatibilidade elétrica.")
        Text("USB-A do notebook é normalmente uma porta de saída de dados/energia, não uma entrada para carregar o notebook.")
    }
}
