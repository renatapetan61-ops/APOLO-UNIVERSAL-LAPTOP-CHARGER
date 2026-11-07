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

## O que já existe

- Aplicativo Android Kotlin + Jetpack Compose com Painel, Bateria, BMS, Conexão e Sobre.
- Simulador local selecionável: Normal, Alerta e Falha.
- Indicadores demonstrativos identificados como simulados.
- Aviso permanente de segurança e indicação de que a saída está bloqueada.
- Decoder binário de telemetria v1, somente leitura, com validação de tamanho, magic, versão, CRC e faixas de plausibilidade.
- Testes unitários do decoder.
- GitHub Actions executa testes, compila APK debug e publica o APK como artefato por 14 dias.
- Documentação de arquitetura, compatibilidade, protocolo, requisitos do BMS e status de desenvolvimento.

## Estrutura

- `android/`: aplicativo Android.
- `bms/`: requisitos e princípios de segurança do BMS proprietário.
- `power-module/`: arquitetura preliminar do módulo.
- `protocols/`: protocolo de telemetria read-only.
- `simulator/`: descrição do simulador local.
- `docs/`: arquitetura, compatibilidade e estado do projeto.
- `.github/workflows/`: CI e artefato APK.

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
- Projeto elétrico completo do pack, carregador AC, conversores, saídas e proteções.
- Transporte USB/BLE implementado e testado com hardware.
- Negociação USB-C PD e perfis DC validados.
- Testes em bancada, integração, falhas, térmica, EMC e certificações aplicáveis.
- Instalação e teste do APK em aparelhos Android físicos.
- Protótipo físico, documentação de fabricação e validação por engenharia qualificada.

Consulte `docs/DEVELOPMENT_STATUS.md` para o relatório de implementação e pendências.
