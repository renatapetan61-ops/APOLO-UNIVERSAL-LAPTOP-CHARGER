# APOLO Universal Laptop Charger

Projeto integrado de aplicativo Android, simulador e arquitetura de referência para um módulo portátil de energia com BMS proprietário.

> **Estado real do projeto:** o aplicativo Android compila no CI. O painel e os três cenários do simulador são locais e demonstrativos. O decoder de telemetria é somente leitura. Nenhum hardware, bateria, BMS físico ou saída de carregamento está conectado ou validado.

## Metas conceituais (não são especificação de fabricação)

| Item | Meta |
|---|---:|
| Energia nominal | 1.500 Wh |
| Potência máxima pretendida | 240 W |
| Química pretendida | LiFePO4 |
| Entrada AC pretendida | 100–240 V AC |
| Barramento de referência | 16S / 51,2 V nominal |
| Saída DC pretendida | 19 V |
| USB-C | USB Power Delivery, com negociação e hardware apropriado |

19 V não é universal: cada notebook exige confirmação de tensão, corrente, polaridade, conector e identificação/protocolo do fabricante.

## Diagnóstico APOLO e chips virtuais

- Quatro controladores de software independentes: APOLO-BMS IC, APOLO-CHARGE IC, APOLO-SAFETY IC e APOLO-USB-PD IC.
- Motor de sensores virtuais que aceita somente observações identificadas do sistema operacional; não inventa leituras físicas.
- Endpoint local do agente `POST /v1/diagnostics/run`, executado sob solicitação explícita do usuário.
- Tela **Reparar** no aplicativo Android e relatório final em pop-up dentro do próprio aplicativo.
- Relatório diferencia erros encontrados, erros corrigidos e erros não corrigidos. Nesta etapa o agente é somente leitura e declara zero correções até existir uma ação segura com pós-condição verificada.
- Os controladores virtuais são software executável, não chips físicos, não sensores físicos e não têm acesso mágico a componentes da placa-mãe.

## O que já existe

- Aplicativo Android Kotlin + Jetpack Compose com Painel, Bateria, BMS, Conexão e Sobre.
- Simulador local selecionável: Normal, Alerta e Falha.
- Indicadores demonstrativos identificados como simulados.
- Aviso permanente de segurança e indicação de que a saída está bloqueada.
- Decoder binário de telemetria v1, somente leitura, com validação de tamanho, magic, versão, CRC e faixas de plausibilidade.
- Testes unitários do decoder.
- GitHub Actions executa testes, compila APK debug e publica o APK como artefato por 14 dias.
- Agente host read-only para inventário de hardware/firmware e telemetria exposta pelo sistema operacional.
- Especificação preliminar do sensor interno DC e contrato de telemetria autenticada (hardware ainda não construído).

## Estrutura

- `android/`: aplicativo Android.
- `bms/`: requisitos e princípios de segurança do BMS proprietário.
- `power-module/`: arquitetura preliminar do módulo.
- `hardware/internal-dc-sensor/`: arquitetura do sensor interno DC; ainda sem esquemático de fabricação.
- `protocols/`: protocolo de telemetria read-only e contrato draft do sensor interno.
- `host-agent/`: agente de inventário e diagnóstico read-only, runtime dos quatro ICs virtuais e testes.
- `simulator/`: descrição do simulador local.
- `docs/`: arquitetura, compatibilidade, limites elétricos e roadmap de engenharia.

## Identificação automática da placa-mãe

Consulte [APOLO Motherboard Identification Sensor](hardware/motherboard-identification/README.md). A integração das fontes CameraX Android e UVC, o relay opcional de webcam virtual no Windows e os limites físicos estão documentados em [AMIS Dual Camera Pipeline](hardware/motherboard-identification/AMIS_DUAL_CAMERA_PIPELINE.md). A proposta combina inventário SMBIOS/DMI já disponível no agente host com um futuro módulo óptico macro para leitura OCR de inscrições, condicionado a linha de visão física segura. O código exato da placa-mãe do S2065 permanece desconhecido até a coleta de evidências.

## Sensor interno e agente embarcado

Consulte [Hardware Internal DC Sensor](hardware/internal-dc-sensor/README.md), [protocolo de telemetria](protocols/internal_dc_sensor_v1.md) e [roadmap](docs/INTERNAL_SENSOR_ROADMAP.md). O sensor exige identificação da revisão exata da placa-mãe, projeto eletrônico protegido, firmware em microcontrolador dedicado, calibração e validação em bancada. Não há polaridade confirmada para o S2065 e nenhum circuito deve ser ligado à placa por tentativa.

## Segurança — limites obrigatórios

- Android, API e nuvem nunca são a proteção primária da bateria.
- O BMS requer proteções físicas independentes, fusível, desconexão segura, watchdog e estado seguro em falhas.
- Nenhum comando de ligar/desligar potência real está implementado.
- Não injete energia em uma porta USB-A do notebook; ela normalmente é uma saída.
- Um cabo USB-C para USB-A pode servir para comunicação em cenários compatíveis, mas não carrega o notebook pela porta USB-A.
- Pack LiFePO4 de 1,5 kWh exige projeto, montagem, análise de risco e ensaios por profissionais qualificados.

## Compilar

Abra o projeto no Android Studio ou execute na raiz:

```bash
gradle :android:app:testDebugUnitTest
gradle :android:app:assembleDebug
```

O APK debug é produzido em `android/app/build/outputs/apk/debug/app-debug.apk` e também publicado como artefato da execução do GitHub Actions quando o workflow termina com sucesso.

## O que falta para o produto completo

- Firmware e placa BMS reais, sensores e medição validada.
- Esquemático, BOM e PCB do sensor interno DC, projetados para a revisão exata da placa.
- Firmware MCU e comunicação autenticada com o host agent.
- Integração do sensor à tela Android.
- Projeto elétrico completo do pack, carregador AC, conversores, saídas e proteções.
- Transporte USB/ADB implementado e testado em dispositivos reais; o cabo comum não transfere software para cada componente da placa-mãe.
- Negociação USB-C PD e perfis DC validados.
- Testes em bancada, integração, falhas, térmica, EMC e certificações aplicáveis.
- Instalação e teste do APK em aparelhos Android físicos.
- Protótipo físico, documentação de fabricação e validação por engenharia qualificada.

Consulte `docs/DEVELOPMENT_STATUS.md` para o relatório de implementação e pendências.
