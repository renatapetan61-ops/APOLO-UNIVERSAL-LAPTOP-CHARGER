# AMIS — integração de câmeras e inspeção óptica

## Pipeline compartilhado

A CameraX do telefone e uma câmera USB/UVC ligada ao notebook podem alimentar o mesmo AMIS Virtual Camera Core. Cada quadro mantém origem, horário, tamanho e SHA-256; o Motherboard Vision Engine processa os quadros individualmente e associa o OCR à origem correta. O núcleo mantém metadados por origem; os bytes da imagem são descartados depois do processamento.

- Celular: `POST /v1/virtual-camera/frames` com `X-AMIS-Source: android-camerax`; requer `adb reverse tcp:8765 tcp:8765` autorizado ou execução no mesmo host.
- Câmera macro/endoscópica USB UVC ligada ao notebook: `POST /v1/camera/capture`; requer dispositivo UVC real e OpenCV.
- Estado combinado: `GET /v1/amis/status`; enumera câmeras UVC visíveis ao host e informa as fontes que já enviaram quadros.

## O que “câmera virtual” significa

A câmera virtual é um núcleo de software que recebe, valida, identifica e encaminha imagens de sensores reais. Ela não é um segundo sensor óptico, não cria detalhes que não foram fotografados e não enxerga através de metal, plástico opaco, teclado ou placa de circuito.

## Acesso físico à motherboard

Para fotografar a placa real, a lente precisa ter linha de visão. Se a placa estiver sob uma tampa opaca, é necessário desligar o notebook, desconectar carregador e bateria e permitir acesso seguro por tampa de manutenção/abertura técnica. Uma microcâmera endoscópica pode ajudar somente se existir uma abertura e espaço para introduzir a lente sem tocar ou danificar componentes. Não inserir sondas em portas, frestas elétricas ou perto de circuitos energizados.

Não existe reconstrução óptica confiável da placa escondida apenas combinando duas câmeras externas. Raios X industriais são outra modalidade de inspeção, não uma função de câmera, e não fazem parte deste projeto.

## Identificação e carregamento

O OCR fornece candidatos de texto; a identificação só pode ser confirmada com correspondência exata no catálogo e evidência eletrônica corroborante. Sem evidência suficiente, o resultado continua `UNKNOWN`. A inspeção visual não mede tensão nem polaridade do jack DC. O carregamento permanece bloqueado até que conector, tensão, corrente, polaridade, autenticação e proteções físicas sejam validados por hardware apropriado.

## Privacidade

O processamento OCR é local. O core descarta os bytes após processamento e conserva apenas metadados operacionais por origem. O cliente Android apaga o arquivo temporário após a transmissão.