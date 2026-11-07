# Arquitetura do APOLO

## Limites de responsabilidade

1. **Android:** interface, visualização, diagnóstico e configuração não crítica.
2. **Power Module:** pack, conversão DC/DC, entrada AC, saídas, sensores, desconexão e invólucro.
3. **BMS interno:** aquisição de medições, estimativa de estado, balanceamento e proteção em hardware/firmware.
4. **Safety supervisor:** lógica de supervisão independente; não substitui comparadores, fusíveis, contactores/MOSFETs e desligamento físico.
5. **Simulador:** fornece telemetria fictícia para desenvolver a UI sem hardware.

## Fluxo

Android ⇄ camada de transporte validada ⇄ gateway do módulo ⇄ BMS/telemetria.

O Android não comanda diretamente gates, contactores, carregadores ou conversores. A autorização de potência, quando e se implementada, deve ser local ao módulo, sujeita a intertravamentos independentes.

## Arquitetura de referência elétrica

16S LiFePO4 é apenas um ponto de partida conceitual: 16 × 3,2 V = 51,2 V nominais. A seleção de células, limites de carga/descarga, fusíveis, condutores, isolamento, dissipação, contatores, pré-carga e conversores depende de engenharia e datasheets específicos.

240 W em 19 V corresponde a aproximadamente 12,63 A no lado de saída, sem incluir perdas. A conversão precisa ser dimensionada para condições de falha e temperatura.

## Estratégia de linguagens

- C/C++ ou Rust embarcado: firmware e drivers, após seleção do MCU e revisão de segurança.
- Go: serviço de telemetria/API.
- Python: testes, análise e ferramentas de bancada.
- Kotlin: Android.
- C#, Java, Ruby, Fortran e D: ferramentas auxiliares somente quando houver necessidade concreta. Não criar serviços redundantes apenas para usar linguagens.

## Fases

- F0: requisitos, riscos e arquitetura.
- F1: aplicativo e simulador local.
- F2: protocolo e testes de integração sem potência.
- F3: protótipo eletrônico em bancada com fontes limitadas e instrumentação.
- F4: validação independente, análise de falhas, ensaios e conformidade.
- F5: integração com pack e conversores somente após aprovação das fases anteriores.
