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
