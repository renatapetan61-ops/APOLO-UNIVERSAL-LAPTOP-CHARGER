# APOLO — arquitetura de eletrônica de potência e controle

**Estado: arquitetura de engenharia em definição. Nenhum circuito desta especificação foi fabricado, energizado ou validado. Não usar como instrução de montagem.**

## Objetivo

Integrar internamente no APOLO Power Module:
1. pack de bateria e proteção física independente;
2. BMS próprio do produto (firmware e supervisão próprios), sem confundir software com o circuito de proteção;
3. controlador de carga bidirecional;
4. controlador USB-C Power Delivery, se USB-C PD for incluído como interface de entrada/saída;
5. conversor regulado de saída DC para o perfil de notebook Positivo PA-1650-65: 19 V, 3,42 A, 64,98 W nominais.

"Interno" significa componentes e placa(s) instalados dentro do invólucro do Power Module. Não significa que um chip de silício possa ser recriado em software.

## Limite entre projeto próprio e chips semicondutores

BQ25756 e TPS25751A são circuitos integrados físicos proprietários. Não é realista nem tecnicamente correto afirmar que um repositório de software recriou seus transistores, drivers analógicos, comparadores, ADCs, proteção de pinos, osciladores e processo de fabricação.

Caminho recomendado para um protótipo funcional:
- usar os CIs físicos originais ou alternativas com datasheets e suporte adequados;
- desenvolver placa e integração APOLO próprias;
- escrever firmware de supervisão/configuração próprio;
- desenvolver BMS próprio do produto, usando AFE/monitor de células e elementos físicos de proteção adequados;
- não clonar firmware proprietário nem assumir compatibilidade de registradores sem documentação autorizada.

Uma substituição integral por semicondutor próprio exigiria projeto analógico/digital, verificação, tape-out, fabricação em foundry, encapsulamento, caracterização e certificação. Isso é um projeto industrial de semicondutores, não uma implementação apenas em C/Rust.

## Funções e fronteiras dos componentes

### BMS APOLO

O BMS é um subsistema próprio e interno do produto, composto por:
- AFE/monitor físico de células apropriado à química e ao número de células;
- medições de corrente e temperatura reais;
- proteção física independente (comparadores/AFE, drivers e MOSFETs/contatores dimensionados, fusível e outros dispositivos definidos por análise de risco);
- MCU de segurança com watchdog e firmware;
- telemetria autenticada para o aplicativo.

O caminho de corte físico não pode depender do Android, de Wi-Fi/Bluetooth, de uma aplicação Linux ou de um processo de alto nível. O estado após reset, perda de alimentação, watchdog ou sensor inválido deve ser seguro e definido pelo projeto de hardware. O circuito deve ser analisado por profissional habilitado e ensaiado com procedimentos e instrumentação apropriados.

### BQ25756

O BQ25756 é um controlador carregador buck-boost bidirecional para baterias de 1 a 14 células, com ADC integrado e interface de controle. É um componente de gerenciamento de conversão/carga, não o BMS completo do pack e não substitui proteção independente de células.

Integração proposta:
- BQ25756 físico em PCB interna, se a seleção de química, topologia, faixa de tensão e requisitos elétricos confirmarem sua adequação;
- firmware APOLO em C para acesso controlado aos registradores documentados via I²C;
- camada Rust para política, telemetria, diagnóstico e comunicação com o app, se a MCU/plataforma suportar Rust embarcado;
- ferramentas Python para geração de casos de teste, análise de logs e calibração;
- estados de falha e intertravamentos implementados no hardware, não apenas na aplicação.

Não implementar mapa de registradores, valores de configuração ou limites sem conferir a revisão vigente do datasheet e o projeto elétrico aprovado. Não assumir que este CI é adequado antes de definir pack e carregador.

### TPS25751A

O TPS25751A é um controlador USB-C/USB Power Delivery com gerenciamento de caminhos de energia, interfaces I²C e recursos de proteção integrados. É um chip físico com firmware/configuração específica do fabricante.

Integração proposta:
- TPS25751A físico em PCB interna somente se a revisão de arquitetura confirmar necessidade de USB-C PD;
- utilizar ferramenta, documentação, patch/configuração e processo oficiais da TI;
- firmware APOLO em C/Rust supervisiona status, intertravamentos e comunicação documentada;
- a negociação PD não pode, por si só, habilitar a saída de 19 V para o notebook;
- caminho da bateria e conversão DC de 19 V permanecem funções separadas, com proteções independentes.

O TPS25751A não é necessário para a saída DC fixa de 19 V quando o módulo opera exclusivamente com bateria interna e sem porta USB-C PD. Sua inclusão depende das interfaces USB-C desejadas para recarga ou fornecimento de energia a outros equipamentos.

## Linguagens e ferramentas

| Tecnologia | Responsabilidade |
|---|---|
| C (C11/C17) | Firmware de MCU, drivers I²C/SPI/ADC, watchdog e interfaces de hardware |
| Rust (no_std quando adequado) | Supervisão segura, máquina de estados, protocolo de telemetria e diagnósticos |
| SystemVerilog | Lógica digital determinística opcional em FPGA; não substitui circuitos analógicos nem proteção física |
| Python | Testes automatizados, análise de logs, ferramentas de calibração e HIL |
| KiCad | Esquemáticos, PCB, footprints, BOM e revisão elétrica |
| SPICE | Simulação de circuitos analógicos como ferramenta de análise; não prova que o circuito físico funciona |

Não se deve escrever código que acione MOSFETs ou habilite potência real antes de existir um projeto elétrico revisado, hardware de proteção independente e plano de testes aprovado.

## Sensores físicos e corte independente

Sensores reais precisam de transdutores e interfaces físicas:
- tensão por célula/grupo: AFE/monitor de bateria;
- corrente: shunt com amplificador de corrente ou sensor apropriado, com faixa e dissipação calculadas;
- temperatura: NTC/RTD ou sensor qualificado em pontos definidos pela análise térmica;
- saída DC: medição independente de tensão/corrente;
- diagnóstico: detecção de fio aberto/curto, referência inválida, ADC saturado, sensor congelado e perda de comunicação.

Proteções independentes devem cobrir, conforme análise de risco:
- sobretensão/subtensão de célula e barramento;
- sobrecorrente e curto-circuito;
- temperatura fora da janela permitida pelas células e componentes;
- falha de sensor, referência, clock, watchdog ou comunicação;
- falha de MOSFET/contator e pré-carga quando aplicável.

Não há valores numéricos de corte neste documento. Eles dependem do fabricante/modelo exato das células, topologia, componentes e condições térmicas. O desenho deve incluir coordenação entre proteção primária e secundária, fusível e capacidade de interrupção.

## Critérios para habilitar potência

O projeto de software deve manter a saída desabilitada até que:
- a identificação do pack e os limites estejam aprovados;
- BMS físico e proteções independentes tenham passado em ensaios;
- leituras reais tenham identidade, calibração, timestamp e plausibilidade válidos;
- conversor DC-DC tenha sido validado em carga eletrônica na faixa de operação;
- a medição independente confirme a saída dentro dos limites aprovados;
- conector e polaridade do notebook estejam confirmados;
- revisão de segurança e conformidade esteja concluída.

## Etapas de desenvolvimento

1. Requisitos de autonomia, peso, volume, química e recarga.
2. Seleção de células rastreáveis e definição de topologia por engenharia.
3. Seleção de AFE/BMS, MOSFETs/contatores, sensores, fusíveis e conversores.
4. Estudo de viabilidade e esquemático em KiCad com revisão independente.
5. Protótipo de baixa energia para validar aquisição de sinais e firmware, sem pack de alta energia.
6. Protótipo de potência testado com fonte de bancada limitada e carga eletrônica, em laboratório.
7. Validação do pack e ensaios de falha/temperatura por equipe qualificada.
8. Integração Android, documentação, avaliação regulatória e testes finais.

## Estado atual

- Documentação de arquitetura: criada.
- Firmware de supervisão BMS: modelo de software existente, sem conexão a sensores físicos.
- BMS/AFE físico APOLO: não construído.
- Sensores e circuito de corte: não construídos.
- BQ25756/TPS25751A: nenhum chip instalado ou integrado em hardware.
- Firmware de controle de potência: não aprovado para acionar hardware.
- Saída de notebook: bloqueada; não existe protótipo validado.
