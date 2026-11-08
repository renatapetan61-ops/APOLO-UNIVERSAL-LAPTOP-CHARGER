# APOLO Power Module — arquitetura com bateria interna

**Status: especificação de engenharia. Não é esquema elétrico, BOM aprovado, firmware de proteção ou autorização para fabricar/energizar o pack.**

## 1. Requisito de saída inicial

O primeiro perfil de compatibilidade é baseado exclusivamente na etiqueta informada do adaptador Positivo PA-1650-65:

- Saída nominal: **19 V DC**
- Corrente nominal: **3,42 A**
- Potência nominal calculada: **64,98 W**
- Entrada do adaptador original: 100–240 V AC, 50–60 Hz, 2,0 A (não é requisito de entrada do módulo).

A saída APOLO deverá ser regulada em 19 V e projetada para entregar pelo menos a carga nominal de 64,98 W continuamente, com margem térmica/elétrica definida na revisão de engenharia. O plugue, dimensões, polaridade, pinagem e tolerância de entrada do notebook continuam **não verificados**. Não conectar ao notebook até confirmar esses dados e validar o conjunto em bancada.

## 2. Arquitetura funcional

Fluxo conceitual de energia:

`Pack de células` → `fusível principal próximo ao pack` → `proteção física independente/BMS AFE` → `chaveamento de segurança + pré-carga quando requerido` → `barramento DC interno` → `conversor DC-DC regulado` → `medição independente de saída` → `chave de saída normalmente desligada` → `conector de saída selecionado`.

Fluxo de supervisão:

`sensores físicos de célula/corrente/temperatura` → `AFE/BMS dedicado` → `MCU de segurança` → `telemetria autenticada` → `APOLO Android app`.

O Android é interface e diagnóstico. Não é o controlador primário de segurança e não pode ser necessário para interromper corrente em uma falha.

## 3. Química e capacidade ainda não selecionadas

A escolha de química, fabricante/modelo de célula, capacidade, quantidade de células em série/paralelo, corrente máxima, energia total e dimensões do pack permanece **TBD**. O repositório anteriormente mencionava LiFePO4/1.500 Wh/240 W como conceito preliminar; isso não foi confirmado pelo usuário nem validado e não deve ser tratado como especificação de compra.

A seleção deve considerar, em conjunto:
- disponibilidade de células legítimas com datasheet e rastreabilidade;
- limites de carga/descarga, temperatura e corrente contínua/pico;
- energia útil desejada, peso, volume e autonomia;
- compatibilidade entre tensão mínima/máxima do pack e faixa de entrada do conversor;
- dissipação térmica, contenção mecânica, vibração e proteção contra curto;
- carregador compatível com a química e topologia exatas;
- análise de risco e requisitos regulatórios aplicáveis.

Não misturar células de modelos, capacidades, idades ou estados de saúde diferentes. Não definir limites numéricos de corte antes de selecionar as células e validar o projeto com profissional qualificado.

## 4. BMS físico e camadas de proteção

O BMS físico deverá incluir, conforme análise de risco e componentes selecionados:
- monitoramento de cada célula/grupo em série;
- medição de corrente do pack e diagnóstico de plausibilidade;
- sensores de temperatura em pontos críticos;
- proteção independente de sobretensão/subtensão, sobrecorrente/curto e temperatura;
- balanceamento compatível com as células;
- watchdog, diagnóstico de sensores abertos/em curto e falhas de comunicação;
- fusível físico dimensionado para o pack e o condutor;
- chaveamento de carga/descarga dimensionado e estado seguro normalmente desligado;
- pré-carga e detecção de falha de chaveamento quando a arquitetura exigir;
- registro de falhas e bloqueio até condição de recuperação validada.

A proteção de hardware deve continuar funcionando se Android, MCU de aplicação ou comunicação travarem. O BMS Kotlin existente é somente um avaliador de telemetria e **não** substitui esses circuitos.

## 5. Conversão para 19 V

A tensão do pack varia durante descarga. Portanto, não se pode ligar o pack diretamente à saída. É necessário um conversor DC-DC regulado cuja faixa de entrada cubra a tensão mínima e máxima reais do pack, com capacidade contínua e térmica adequada à saída de 19 V / 3,42 A.

A saída deve ter medição própria de tensão/corrente, proteção contra sobretensão, sobrecorrente, curto e sobretemperatura, descarga controlada do barramento quando necessário e chaveamento físico independente. A saída deve permanecer desabilitada durante inicialização, falha, telemetria inválida ou falta de autenticação/configuração.

Nenhum valor de tolerância de saída, limite de corte, componente ou layout está aprovado neste documento.

## 6. Recarga da bateria interna

Escolher bateria interna como fonte de energia não define como o pack será recarregado. A entrada de recarga é uma função separada e ainda está TBD.

A solução futura deve usar carregador dedicado à química e à configuração série/paralelo selecionadas, com perfil CC/CV ou algoritmo exigido pelo fabricante da célula, sensores térmicos e intertravamentos. Não carregar células diretamente por USB, por uma fonte genérica ou pelo conversor de saída de 19 V.

A opção de recarga por rede elétrica exige fonte/carregador isolado certificado e avaliação de segurança por profissional habilitado. USB-C PD pode ser estudado como entrada auxiliar em uma etapa posterior, mas não é a fonte de energia escolhida para alimentar o notebook.

## 7. Sequência de habilitação da saída

A saída física somente poderá ser considerada para habilitação depois de todos os itens abaixo serem implementados e validados:

1. Pack e células identificados por fabricante/modelo e rastreabilidade.
2. Topologia elétrica e limites aprovados para aquelas células.
3. BMS/AFE e proteções independentes instalados e testados.
4. Sensores reais calibrados e telemetria autenticada/fresca.
5. Conversor DC-DC validado em carga eletrônica e em toda a faixa de tensão do pack.
6. Medição de saída independente confirma tensão dentro da janela aprovada.
7. Polaridade e conector do notebook confirmados por documentação/medição apropriada.
8. Ensaios de falha, térmica, EMC, mecânica e segurança concluídos.
9. Revisão técnica e regulatória concluída.

Até lá, software deve manter `physicalOutputPermitted = false`. Não usar bateria real nem notebook real em testes de firmware ou protótipo não validado.

## 8. Plano de validação por etapas

- **Etapa A — requisitos:** selecionar perfil de uso/autonomia, química e células; análise de risco.
- **Etapa B — projeto:** revisão esquemática, seleção de componentes, térmica, mecânica e proteção.
- **Etapa C — bancada de baixa energia:** validar sensores, telemetria, watchdog e lógica com fontes limitadas e simuladores de sinal; isso não é teste de pack.
- **Etapa D — protótipo profissional:** testes com carga eletrônica e instrumentação apropriada, sem notebook conectado.
- **Etapa E — validação do pack:** ensaios conduzidos por equipe qualificada, com contenção e procedimentos de segurança.
- **Etapa F — integração:** somente após aprovação das etapas anteriores, testar com equipamento compatível e monitoramento.

## 9. Dados que ainda precisam ser definidos

- Autonomia desejada em carga próxima de 65 W.
- Limite de peso e dimensões aceitáveis.
- Química/modelo de célula e capacidade final.
- Método de recarga e tempo de recarga desejado.
- Confirmação física/documental do plugue e polaridade do Positivo.
- Outros perfis de notebook além do Positivo 19 V.

## 10. Estado atual

- Perfil de saída de referência: 19 V / 3,42 A / 64,98 W, derivado da etiqueta do adaptador.
- BMS de software: avaliador fail-closed, sem controle de atuadores.
- Pack físico, BMS/AFE, sensores reais, conversor, carregador e conector: não construídos/não validados.
- Saída real: bloqueada.
