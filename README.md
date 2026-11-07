# APOLO Universal Laptop Charger

Plataforma Android + módulo portátil de energia + BMS proprietário para diagnóstico e integração de alimentação de notebooks.

> **Status:** fundação de software. O app inclui modo demonstração; não controla saídas de potência reais. Hardware e BMS ainda não foram construídos nem validados.

## Metas preliminares (não são especificação de fabricação)

| Item | Meta |
|---|---:|
| Energia nominal | 1.500 Wh |
| Potência máxima pretendida | 240 W |
| Química | LiFePO4 |
| Entrada AC do carregador | 100–240 V AC |
| Barramento de referência | 16S / 51,2 V nominal |
| Saída DC pretendida | 19 V |
| USB-C | USB Power Delivery, com negociação e hardware apropriado |

A compatibilidade com notebooks depende de tensão, corrente, polaridade, conector e identificação/protocolo do fabricante. 19 V não é universal.

## Componentes

- `android/`: aplicativo Kotlin + Jetpack Compose.
- `power-module/`: especificação de arquitetura do módulo.
- `bms/`: arquitetura e requisitos do BMS proprietário.
- `protocols/`: protocolo de telemetria.
- `simulator/`: simulador de dados para desenvolvimento.
- `docs/`: arquitetura, segurança e compatibilidade.
- `.github/workflows/`: validação automatizada.

## Segurança

- Android, API e nuvem nunca são a proteção primária da bateria.
- O BMS requer proteções físicas independentes, fusível, desconexão segura, watchdog e estado seguro em falhas.
- Nenhum comando de ligar/desligar potência real é implementado nesta versão.
- Não injete energia em uma porta USB-A do notebook. Em geral, ela é uma saída de energia, não uma entrada de carregamento.
- Cabo USB-C para USB-A pode ser usado para comunicação em cenários compatíveis; não fornece energia suficiente para carregar um notebook.
- Pack LiFePO4 de 1,5 kWh exige projeto, montagem, análise de risco e ensaios por profissionais qualificados.

## Começar

Abra a pasta `android/` no Android Studio (AGP/Gradle conforme os arquivos do projeto), sincronize e execute o app em um dispositivo Android compatível. O painel inicia em modo DEMO e identifica claramente os dados simulados.

## Estado

| Área | Situação |
|---|---|
| Estrutura Android | Inicial |
| Painel demonstrativo | Implementado nesta base |
| Simulador | Inicial |
| Comunicação física | Interface planejada; ainda sem driver validado |
| BMS/firmware | Requisitos e arquitetura, sem controle de potência |
| Hardware/certificação | Não implementados |

Consulte `docs/ARCHITECTURE.md`, `docs/POWER_COMPATIBILITY.md` e `bms/SAFETY_REQUIREMENTS.md`.
