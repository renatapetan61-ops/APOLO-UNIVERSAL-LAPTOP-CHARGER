# APOLO Power Module

Subsistema físico previsto para armazenar energia em bateria interna e fornecer saídas reguladas para notebooks compatíveis.

## Perfil inicial de saída

O primeiro perfil de referência é baseado na etiqueta do adaptador Positivo PA-1650-65 informada pelo usuário:

- 19 V DC
- 3,42 A
- 64,98 W nominais (19 × 3,42)

A polaridade, dimensões e pinagem do conector DC do notebook ainda não foram verificadas. A compatibilidade física/elétrica não está confirmada.

## Estado de engenharia

A arquitetura com bateria interna, BMS físico independente, conversor DC-DC, proteções, recarga e critérios de habilitação está documentada em [INTERNAL_BATTERY_ARCHITECTURE.md](INTERNAL_BATTERY_ARCHITECTURE.md).

Química, fabricante/modelo das células, topologia série/paralelo, capacidade, energia, limites de corrente, carregador, conversores, fusíveis, chaveamento, conectores, térmica, invólucro e certificações permanecem TBD até seleção e validação de engenharia.

Qualquer referência anterior a LiFePO4, 1.500 Wh ou 240 W é apenas conceito preliminar, não especificação final aprovada.

## Segurança

- O BMS de software do aplicativo não substitui proteção física independente.
- A saída de 19 V deve permanecer desabilitada até que pack, BMS/AFE, sensores, conversor, proteções, conector e polaridade sejam validados.
- Não conectar protótipos não validados ao notebook nem carregar células diretamente por USB ou fonte genérica.
- Não há esquema elétrico, BOM aprovado, protótipo físico ou ensaio de segurança concluído neste repositório.
