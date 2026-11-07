# Protocolo APOLO — rascunho de telemetria

## Objetivo

Definir mensagens de leitura entre o aplicativo e o módulo. A primeira versão é somente leitura. Não há opcode para habilitar saída, alterar limites de proteção ou comandar contatores.

## Envelope lógico

- `version`: versão do protocolo.
- `message_type`: `telemetry`, `health`, `fault` ou `identity`.
- `sequence`: contador monotônico.
- `timestamp_ms`: relógio monotônico do módulo.
- `payload`: campos tipados.
- `crc`: integridade do quadro na camada de transporte.

## Telemetria

Exemplo ilustrativo, não proveniente de hardware:

```json
{
  "version": 1,
  "message_type": "telemetry",
  "sequence": 42,
  "timestamp_ms": 120000,
  "payload": {
    "mode": "SAFE_OFF",
    "soc_percent": 78.0,
    "pack_voltage_v": 51.2,
    "pack_current_a": 0.0,
    "temperature_c": 25.0,
    "output_enabled": false,
    "data_origin": "SIMULATOR"
  }
}
```

## Regras

- Rejeitar versão desconhecida, tamanho inválido, CRC incorreto e sequência regressiva.
- Marcar telemetria expirada como indisponível, nunca reutilizar silenciosamente valores antigos.
- Unidade SI explícita em todos os campos.
- Campos de origem devem distinguir `SIMULATOR` de `HARDWARE`.
- Qualquer futuro comando não telemétrico exige threat model, autenticação, autorização local e revisão de segurança separada.
