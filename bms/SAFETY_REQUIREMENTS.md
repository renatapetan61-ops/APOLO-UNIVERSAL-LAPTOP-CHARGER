# Requisitos de segurança — BMS proprietário

Este documento é uma especificação de requisitos, não firmware pronto para controlar um pack.

## Monitoramento requerido

- tensão de cada célula/grupo;
- corrente do pack com medição redundante ou plausibilidade independente conforme análise de risco;
- múltiplos sensores de temperatura em pontos críticos;
- estado de carga (SoC) e saúde (SoH) com indicação de incerteza;
- tensão do barramento e estado de isolamento quando aplicável;
- detecção de sensor aberto, em curto, congelado ou fora de faixa.

## Condições de falha a tratar

- sobretensão/subtensão de célula;
- sobrecorrente de carga/descarga e curto-circuito;
- sobretemperatura/subtemperatura;
- falha de medição, ADC, referência, comunicação ou watchdog;
- divergência entre sensores;
- falha de contactor/MOSFET soldado ou aberto;
- falha de pré-carga e tensão inesperada no barramento.

## Princípios obrigatórios

- Estado seguro por padrão e saída desabilitada após reset.
- Proteção independente do Android, da rede e do processador principal.
- Fusível físico e dispositivo de desconexão dimensionados por engenharia.
- Limites derivados exclusivamente dos datasheets das células e componentes escolhidos.
- Diagnóstico de falhas persistente e timestamped.
- Watchdog externo e estratégia documentada para perda de alimentação/clock.
- Balanceamento somente dentro dos limites e condições validados.
- Testes de falha injetada em bancada, sem pack de alta energia.

## Não implementado

Nenhum limite numérico de corte, algoritmo de gate drive, esquema elétrico ou firmware de acionamento está aprovado nesta fase. Não construir nem energizar um pack com base apenas neste repositório.
