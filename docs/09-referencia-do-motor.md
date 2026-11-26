# 9. Referência do motor

> **Resumo:** `discord_rpc_injector.py` é um módulo autossuficiente (só biblioteca padrão)
> que você pode importar em qualquer script Python para definir a presença do Discord.

## Exemplo rápido

```python
import time
from discord_rpc_injector import DiscordIPC

ipc = DiscordIPC("1234567890123456789")      # seu Application ID
print("Conectado via", ipc.connect())

ipc.set_activity({
    "details": "Escrevendo documentação",
    "state": "No terminal",
    "timestamps": {"start": int(time.time())},
})

input("Enter para remover a presença…")
ipc.clear_activity()
ipc.disconnect()
```

## `DiscordIPC(client_id)`

Cliente do protocolo IPC local do Discord.

| Membro                     | Descrição                                                              |
|----------------------------|------------------------------------------------------------------------|
| `connect() -> str`         | Encontra o socket, faz o handshake e devolve o caminho usado           |
| `set_activity(activity)`   | Envia `SET_ACTIVITY` com o dicionário dado; devolve a resposta do Discord |
| `clear_activity()`         | Remove a presença (`activity = null`)                                  |
| `disconnect()`             | Envia `CLOSE` e fecha o socket (seguro chamar mais de uma vez)         |
| `candidate_sockets()`      | Gerador com os sockets existentes, em ordem e sem repetir links        |
| `sock`                     | O `socket.socket` aberto, ou `None`                                    |
| `pid`                      | PID enviado ao Discord (o do processo atual)                           |

### Tempos limite (atributos de classe, em segundos)

| Atributo            | Padrão | Quando                                   |
|---------------------|-------:|------------------------------------------|
| `CONNECT_TIMEOUT`   | 2.0    | Abrir a conexão com cada socket          |
| `HANDSHAKE_TIMEOUT` | 12.0   | Esperar o `READY`                        |
| `IO_TIMEOUT`        | 10.0   | Cada envio/resposta depois de conectado  |

Para mudar, crie uma subclasse:

```python
class IPCRapido(DiscordIPC):
    HANDSHAKE_TIMEOUT = 3.0
```

### Erros

| Exceção                       | Quando                                                            |
|-------------------------------|-------------------------------------------------------------------|
| `ConnectionError`             | Nenhum socket encontrado, ou nenhum respondeu (mensagem lista cada caminho e o motivo) |
| `HandshakeRejected`           | O Discord recusou o handshake (ex.: código 4000, ID inválido)     |
| `DiscordClosed`               | O Discord encerrou a conexão; atributo `code` com o código, se houver |
| `socket.timeout` / `TimeoutError` | Uma resposta passou do `IO_TIMEOUT` depois de conectado       |

`HandshakeRejected` e `DiscordClosed` são subclasses de `ConnectionError`.

## Formato de `activity`

Todos os campos são opcionais. Os principais:

```python
{
    "details": str,                       # 1ª linha
    "state": str,                         # 2ª linha
    "timestamps": {"start": int},         # epoch em segundos → "decorrido"
    "assets": {
        "large_image": str, "large_text": str,   # chave do Art Asset + dica
        "small_image": str, "small_text": str,
    },
    "buttons": [{"label": str, "url": str}],     # até 2
    "party": {"id": str, "size": [atual, máximo]},
}
```

## Predefinições

| Nome                        | Descrição                                                         |
|-----------------------------|-------------------------------------------------------------------|
| `config_dir() -> str`       | `$XDG_CONFIG_HOME/discord-rpc-injector` (padrão `~/.config/…`)    |
| `PRESETS_FILE`              | Caminho do `presets.json`                                         |
| `load_presets() -> dict`    | Lê as predefinições; arquivo ausente ou inválido resulta em `{}`  |
| `save_presets(presets)`     | Grava de forma atômica (cria a pasta se preciso)                  |

Formato do `presets.json`: um objeto cujas chaves são os nomes das predefinições:

```json
{
  "Fedora": {
    "app_id": "123456789012345678",
    "details": "Just Chilling",
    "state": "(KDE Plasma)",
    "large_key": "", "large_text": "", "small_key": "", "small_text": "",
    "btn1_label": "", "btn1_url": "", "btn2_label": "", "btn2_url": "",
    "party_size": "", "party_max": "", "party_id": "",
    "show_elapsed": true
  }
}
```

## Outras constantes

| Nome           | Descrição                                                              |
|----------------|------------------------------------------------------------------------|
| `FLATPAK_IDS`  | IDs Flatpak cujos sockets são procurados (Discord, Canary, Vesktop)     |
| `APP_DIR_NAME` | Nome da pasta de configuração (`discord-rpc-injector`)                  |

Para suportar outro cliente Flatpak, basta adicionar o ID dele em `FLATPAK_IDS`.

---

Anterior: [Desenvolvimento](08-desenvolvimento.md) · [Voltar ao índice](README.md)
