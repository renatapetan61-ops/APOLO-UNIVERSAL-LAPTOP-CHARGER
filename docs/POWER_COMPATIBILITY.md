# Compatibilidade de alimentação

## Não existe uma saída universal de 19 V

Antes de alimentar um notebook é obrigatório confirmar:
- tensão nominal e faixa permitida;
- corrente e potência máximas;
- polaridade;
- diâmetro e geometria do conector;
- identificação eletrônica/resistor/protocolo proprietário;
- requisitos de isolamento, ripple, transientes e proteção.

Uma saída DC de 19 V não deve ser conectada a um equipamento sem confirmar todos esses requisitos.

## USB-C Power Delivery

USB-C PD requer controlador de fonte apropriado, negociação de perfil, cabo com classificação adequada e proteções elétricas. A tensão não deve ser aplicada por tentativa ou por pinagem improvisada.

## USB-A do notebook

USB-A no notebook normalmente fornece energia para periféricos. Não injete energia nessa porta para tentar carregar a bateria interna. Um cabo USB-C (celular) para USB-A (notebook) não é fonte de 65/100/240 W.

## Potência e autonomia

A 19 V, 240 W equivalem a cerca de 12,63 A no lado de saída. Autonomia não pode ser prometida a partir da capacidade nominal isolada; deve considerar energia útil, eficiência, limites de descarga, temperatura, envelhecimento e consumo real.

## Perfil inicial: Positivo Unique TV S2065

O projeto registra como referência inicial a informação fornecida pelo usuário sobre o carregador original: **19 V e 3,42 A**, equivalente a **64,98 W**. Esse valor descreve a classificação do adaptador, não confirma sozinho a faixa de entrada do notebook nem a compatibilidade de qualquer fonte substituta.

Ainda não estão confirmados:
- código exato e dimensões do plugue DC;
- polaridade indicada no adaptador e no notebook;
- tolerância de tensão na entrada do equipamento;
- eventual pino de identificação ou requisito proprietário.

O perfil de software permanece explicitamente **não verificado**. Nenhuma saída pode ser autorizada com base apenas nesses dados. A próxima etapa é comparar a etiqueta do adaptador original e a identificação da entrada do notebook, além de validar a geometria do conector e a polaridade com procedimento técnico seguro.
