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
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ApoloApp() }
    }
}

private enum class Screen(val label: String) {
    HOME("Painel"), BATTERY("Bateria"), BMS("BMS"), REPAIR("Reparar"), CONNECTION("Conexão"), ABOUT("Sobre")
}

private enum class DemoScenario(val label: String) {
    NORMAL("Normal"), WARNING("Alerta"), FAULT("Falha")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ApoloApp() {
    var screen by remember { mutableStateOf(Screen.HOME) }
    var scenario by remember { mutableStateOf(DemoScenario.NORMAL) }
    val telemetry = remember(scenario) { DemoData.sample(scenario) }
    MaterialTheme(colorScheme = darkColorScheme()) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("APOLO Charger") },
                    actions = { AssistChip(onClick = {}, label = { Text("SIMULADOR") }) }
                )
            },
            bottomBar = {
                NavigationBar {
                    Screen.entries.forEach { item ->
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
                                        Screen.REPAIR -> Icons.Default.MonitorHeart
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
                    Screen.HOME -> HomeScreen(telemetry, scenario, onScenario = { scenario = it }, onStartConnection = { screen = Screen.CONNECTION })
                    Screen.BATTERY -> BatteryScreen(telemetry)
                    Screen.BMS -> BmsScreen(scenario, telemetry)
                    Screen.CONNECTION -> ConnectionScreen()
                    Screen.REPAIR -> RepairScreen()
                    Screen.ABOUT -> AboutScreen()
                }
            }
        }
    }
}

@Composable
private fun HomeScreen(t: DemoTelemetry, scenario: DemoScenario, onScenario: (DemoScenario) -> Unit, onStartConnection: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Módulo APOLO", style = MaterialTheme.typography.titleLarge)
            Text("Nenhum hardware conectado", color = MaterialTheme.colorScheme.secondary)
            Text("A saída de potência está bloqueada nesta versão.")
            Button(onClick = onStartConnection, modifier = Modifier.fillMaxWidth()) {
                Text("Iniciar preparação e conexão do notebook")
            }
            LinearProgressIndicator(progress = { t.stateOfCharge / 100f }, modifier = Modifier.fillMaxWidth())
            Text("Carga simulada: ${t.stateOfCharge}%")
        }
    }
    Text("Cenário de teste", style = MaterialTheme.typography.titleMedium)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        DemoScenario.entries.forEach { item ->
            FilterChip(
                selected = scenario == item,
                onClick = { onScenario(item) },
                label = { Text(item.label) }
            )
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
    Text("Estado simulado: ${t.status}", style = MaterialTheme.typography.titleSmall)
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
    Text("Meta conceitual: LiFePO4, 1.500 Wh. Capacidade e autonomia reais dependem do pack, conversores, carga e condições térmicas.")
    SafetyNotice()
}

@Composable
private fun BmsScreen(scenario: DemoScenario, t: DemoTelemetry) {
    val assessment = remember {
        InternalBmsCore(profile = null, limits = null).assess(null, System.currentTimeMillis())
    }
    val outputDecision = remember {
        ApoloPowerModuleCore(profile = null).evaluateOutputRequest(
            ApoloOutputRequest(
                type = ApoloOutputType.DC_BARREL,
                requestedVoltageV = 19.0,
                requestedPowerW = 65.0,
                laptopProfileVerified = false
            )
        )
    }
    Text("BMS interno APOLO — software", style = MaterialTheme.typography.headlineMedium)
    ListItem(
        headlineContent = { Text("Avaliação executada pelo núcleo Kotlin") },
        supportingContent = { Text("Estado: ${assessment.state}. ${assessment.reasons.joinToString()}") }
    )
    ListItem(
        headlineContent = { Text("Power Module Core") },
        supportingContent = { Text(if (outputDecision.acceptedForHardware) "Solicitação aceita" else "Solicitação recusada: ${outputDecision.reason}") }
    )
    Text("O BMS é um subsistema de software desenvolvido do zero para integrar o Power Module; não é um produto separado.")
    ListItem(headlineContent = { Text("Motor de avaliação") }, supportingContent = { Text("Implementado em Kotlin: estados normal, alerta, crítico, dados inválidos e não configurado") })
    ListItem(headlineContent = { Text("Estimativa de carga") }, supportingContent = { Text("Estimador básico por contagem de coulombs; ainda não calibrado") })
    ListItem(headlineContent = { Text("Telemetria de células e sensores") }, supportingContent = { Text("Origem atual: SIMULADOR LOCAL. Nenhum ADC, termistor ou monitor de célula físico foi detectado.") })
    ListItem(headlineContent = { Text("Proveniência dos dados") }, supportingContent = { Text("Cada adaptador de sensor deve declarar SIMULATED ou HARDWARE, identidade da fonte, timestamp e integridade. Dados virtuais nunca autorizam saída.") })
    ListItem(headlineContent = { Text("Estado do cenário") }, supportingContent = { Text("${scenario.label}: ${t.status}") })
    ListItem(headlineContent = { Text("Saída de potência") }, supportingContent = { Text("Bloqueada: software não substitui proteção elétrica independente") })
    SafetyNotice()
}

@Composable
private fun AboutScreen() {
    Text("Sobre o projeto", style = MaterialTheme.typography.headlineMedium)
    Text("APOLO Universal Laptop Charger — versão 0.7.0")
    Text("Aplicativo em desenvolvimento. Leituras marcadas como SIMULADO são dados artificiais de teste; leituras reais só aparecem quando uma fonte de sensor identificada e validada estiver conectada. Não há controle de energia nesta versão.")
    Text("Metas de engenharia: até 240 W, 1.500 Wh LiFePO4 e saída DC pretendida de 19 V, sujeitas a projeto, compatibilidade e certificação.")
    SafetyNotice()
}

@Composable
private fun SafetyNotice() {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("SEGURANÇA", style = MaterialTheme.typography.titleSmall)
            Text("Saídas reais permanecem bloqueadas. Os dados são simulados. O app não substitui BMS, fusíveis, desconexão física ou proteções elétricas independentes.")
        }
    }
}

private data class DemoTelemetry(
    val stateOfCharge: Int,
    val packVoltage: String,
    val temperature: String,
    val current: String,
    val power: String,
    val status: String
)

private object DemoData {
    fun sample(scenario: DemoScenario) = when (scenario) {
        DemoScenario.NORMAL -> DemoTelemetry(78, "51,2", "25,0", "0,0", "0", "Operação normal simulada")
        DemoScenario.WARNING -> DemoTelemetry(18, "48,0", "48,0", "0,0", "0", "Atenção: temperatura elevada simulada")
        DemoScenario.FAULT -> DemoTelemetry(8, "44,0", "62,0", "0,0", "0", "Falha crítica simulada — saída bloqueada")
    }
}
