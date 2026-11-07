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
