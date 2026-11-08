# Verificação USB e identidade do Positivo Unique TV S2065

## O que o aplicativo verifica de verdade
A versão 0.4.0 usa Android USB Host API (`UsbManager.deviceList`) para enumerar periféricos USB que o próprio telefone consegue hospedar. Atualiza a leitura ao conectar/desconectar um periférico e oferece atualização manual. Exibe VID/PID e o nome de dispositivo fornecido pelo Android.

## Limitação de topologia
Em uma ligação USB comum entre notebook e telefone, o notebook normalmente atua como USB host e o telefone como dispositivo/periférico (MTP, tethering etc.). Nesse arranjo, o aplicativo Android não recebe a identidade USB do notebook via USB Host. O app não finge que o cabo conectado prova que o notebook é um Positivo S2065.

Para autenticação positiva do notebook, será necessário instalar um agente de software no próprio notebook que responda a um protocolo de desafio-resposta autenticado, ou usar uma interface de comunicação APOLO dedicada. VID/PID e nome anunciados não são autenticação forte e nenhum fingerprint do S2065 foi inventado ou pré-aprovado.

## Polaridade e conector DC
O cabo USB de dados não tem acesso aos contatos do conector de alimentação DC. O app não pode inferir:
- dimensões e geometria do plugue DC;
- posição do pino interno/externo;
- polaridade positiva/negativa;
- tensão real no jack do notebook.

A medição exige um circuito de medição isolado, com limitação de corrente e proteção contra ligação incorreta, conectado ao módulo APOLO e validado por engenharia. Não se deve sondar o jack com fios improvisados nem aplicar tensão experimental.

## Fail-closed
A saída do Power Module continua bloqueada. Uma identificação USB, mesmo futura, nunca libera potência por si só; será necessária validação elétrica independente do perfil, sensores, limites e proteções físicas.


## Núcleos internos adicionados na versão 0.5.0

### Analisador interno de polaridade
`DcPolaritySensorCore` é o analisador de software do sensor APOLO. Recebe uma amostra center-to-sleeve em volts, idade da amostra, indicação de origem ADC autenticada e calibração validada por engenharia. Classifica centro positivo, centro negativo, ambíguo, amostra vencida ou inválida. Sem ADC físico isolado, nenhuma amostra é produzida e o estado fica `NO_MEASUREMENT`. O algoritmo não cria um sensor elétrico por software.

### Identidade criptográfica do notebook
`UsbLaptopAuthentication` implementa o verificador HMAC-SHA256 de desafio-resposta para o futuro agente APOLO instalado no notebook. Rejeita modelo diferente, nonce divergente, chave ausente/fraca ou assinatura inválida. Nenhuma chave é embutida no aplicativo. A autenticação só é possível após provisionamento seguro e implementação do transporte compatível no host.

### Limite de uso
Os dois núcleos são internos ao aplicativo e testados por testes unitários. Eles não ativam a saída DC. O cabo USB comum, sem um protocolo/agente e sem interface de medição elétrica, não consegue fornecer nem a identidade autenticada do host nem a polaridade do jack.
