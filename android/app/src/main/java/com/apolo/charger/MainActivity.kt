package com.apolo.charger

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BatteryChargingFull
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.MonitorHeart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ApoloApp() }
    }
}

private enum class Screen(val label: String) {
    HOME("Painel"), BATTERY("Bateria"), BMS("BMS"), CONNECTION("Conexão"), ABOUT("Sobre")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ApoloApp() {
    var screen by remember { mutableStateOf(Screen.HOME) }
    val telemetry = remember { DemoData.sample() }
    MaterialTheme(colorScheme = darkColorScheme()) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("APOLO Charger") },
                    actions = { AssistChip(onClick = {}, label = { Text("DEMO") }) }
                )
            },
            bottomBar = {
                NavigationBar {
                    listOf(Screen.HOME, Screen.BATTERY, Screen.BMS, Screen.CONNECTION, Screen.ABOUT).forEach { item ->
                        NavigationBarItem(
                            selected = screen == item,
                            onClick = { screen = item },
                            icon = {
                                Icon(
                                    imageVector = when (item) {
                                        Screen.HOME -> Icons.Default.Bolt
                                        Screen.BATTERY -> Icons.Default.BatteryChargingFull
                                        Screen.BMS -> Icons.Default.MonitorHeart
                                        Screen.CONNECTION -> Icons.Default.Build
                                        Screen.ABOUT -> Icons.Default.Info
                                    },
                                    contentDescription = item.label
                                )
                            },
                            label = { Text(item.label) }
                        )
                    }
                }
            }
        ) { padding ->
            Column(
                Modifier.padding(padding).fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                when (screen) {
                    Screen.HOME -> HomeScreen(telemetry)
                    Screen.BATTERY -> BatteryScreen(telemetry)
                    Screen.BMS -> BmsScreen()
                    Screen.CONNECTION -> ConnectionScreen()
                    Screen.ABOUT -> AboutScreen()
                }
            }
        }
    }
}

@Composable
private fun HomeScreen(t: DemoTelemetry) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Módulo APOLO", style = MaterialTheme.typography.titleLarge)
            Text("Nenhum hardware conectado", color = MaterialTheme.colorScheme.secondary)
            Text("A saída de potência está bloqueada nesta versão.", style = MaterialTheme.typography.bodyMedium)
            LinearProgressIndicator(progress = { t.stateOfCharge / 100f }, modifier = Modifier.fillMaxWidth())
            Text("Carga simulada: ${t.stateOfCharge}%")
        }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        MetricCard("Tensão", "${t.packVoltage} V", Modifier.weight(1f))
        MetricCard("Temperatura", "${t.temperature} °C", Modifier.weight(1f))
    }
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        MetricCard("Corrente", "${t.current} A", Modifier.weight(1f))
        MetricCard("Potência", "${t.power} W", Modifier.weight(1f))
    }
    SafetyNotice()
}

@Composable
private fun MetricCard(title: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text(title, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.secondary)
            Text(value, style = MaterialTheme.typography.titleLarge)
            Text("SIMULADO", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.tertiary)
        }
    }
}

@Composable
private fun BatteryScreen(t: DemoTelemetry) {
    Text("Bateria", style = MaterialTheme.typography.headlineMedium)
    MetricCard("Estado de carga (SoC)", "${t.stateOfCharge}%")
    MetricCard("Barramento de referência", "${t.packVoltage} V")
    MetricCard("Temperatura simulada", "${t.temperature} °C")
    Text("Meta de projeto: LiFePO4, 1.500 Wh. A capacidade real e a autonomia dependem do pack validado, conversores, carga e condições térmicas.")
    SafetyNotice()
}

@Composable
private fun BmsScreen() {
    Text("BMS proprietário", style = MaterialTheme.typography.headlineMedium)
    listOf(
        "Monitoramento individual de células: não conectado",
        "Corrente e tensão do pack: dados simulados",
        "Sensores térmicos: não conectados",
        "Balanceamento: desabilitado",
        "Registro de falhas: somente demonstração",
        "Desconexão independente: requisito de hardware"
    ).forEach { ListItem(headlineContent = { Text(it) }) }
    SafetyNotice()
}

@Composable
private fun ConnectionScreen() {
    Text("Conectividade", style = MaterialTheme.typography.headlineMedium)
    ListItem(headlineContent = { Text("USB") }, supportingContent = { Text("Host USB opcional; nenhum dispositivo detectado") })
    ListItem(headlineContent = { Text("Bluetooth") }, supportingContent = { Text("Integração ainda não implementada") })
    ListItem(headlineContent = { Text("Protocolo APOLO") }, supportingContent = { Text("Especificação inicial em protocols/TELEMETRY_PROTOCOL.md") })
    Text("O cabo USB-C para USB-A pode ser útil para comunicação em combinações compatíveis. Ele não transforma a porta USB-A do notebook em entrada de carga.")
    SafetyNotice()
}

@Composable
private fun AboutScreen() {
    Text("Sobre o projeto", style = MaterialTheme.typography.headlineMedium)
    Text("APOLO Universal Laptop Charger — versão 0.1.0")
    Text("Aplicativo em fase inicial. O modo atual é demonstração local, sem conexão com bateria ou controle de energia.")
    Text("Metas: até 240 W, 1.500 Wh LiFePO4 e saída DC pretendida de 19 V, sujeitas a projeto e validação.")
    SafetyNotice()
}

@Composable
private fun SafetyNotice() {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("SEGURANÇA", style = MaterialTheme.typography.titleSmall)
            Text("Saídas reais permanecem bloqueadas. Dados exibidos são demonstrativos. O app não substitui o BMS nem proteções elétricas independentes.")
        }
    }
}

private data class DemoTelemetry(
    val stateOfCharge: Int,
    val packVoltage: String,
    val temperature: String,
    val current: String,
    val power: String
)

private object DemoData {
    fun sample() = DemoTelemetry(
        stateOfCharge = 78,
        packVoltage = "51,2",
        temperature = "25,0",
        current = "0,0",
        power = "0"
    )
}
