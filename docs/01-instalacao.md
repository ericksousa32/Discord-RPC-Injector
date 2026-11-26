# 1. Instalação

> **Resumo:** instale o PySide6, rode `python3 main.py` e, se quiser, crie o atalho no menu
> com `python3 main.py --install-desktop`. Nada disso precisa de `sudo`, exceto instalar
> pacotes pelo gerenciador da sua distro.

## Requisitos

| O quê      | Versão mínima | Para quê                                             |
|------------|---------------|------------------------------------------------------|
| Python     | 3.8           | Motor (só usa a biblioteca padrão)                   |
| PySide6    | 6.5           | Interface gráfica (Qt)                               |
| Discord    | qualquer      | Nativo, Flatpak ou Snap, aberto e logado             |

O motor funciona sozinho, sem PySide6. A interface precisa do PySide6 6.5 ou mais novo
porque usa a detecção de tema claro/escuro do Qt.

## Instalando as dependências

### Fedora (e derivadas)

```bash
sudo dnf install python3-pyside6
```

### Ubuntu / Debian (e derivadas)

```bash
sudo apt install python3-pyside6.qtwidgets python3-pyside6.qtsvg
```

Confira a versão com `python3 -c "import PySide6; print(PySide6.__version__)"`. Se for
anterior à 6.5, ou se o pacote não existir na sua versão da distro, use o venv abaixo.

### Qualquer distro, com venv (sem tocar no sistema)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Depois use `.venv/bin/python` no lugar de `python3` nos comandos desta página.

## Abrindo o app

Na pasta do projeto:

```bash
python3 main.py
```

## Atalho no menu de aplicativos

```bash
python3 main.py --install-desktop
```

Isso cria, só para o seu usuário:

| Arquivo                                                            | O que é              |
|--------------------------------------------------------------------|----------------------|
| `~/.local/share/applications/discord-rpc-injector.desktop`         | Atalho do menu       |
| `~/.local/share/icons/hicolor/scalable/apps/discord-rpc-injector.svg` | Ícone vetorial    |
| `~/.local/share/icons/hicolor/256x256/apps/discord-rpc-injector.png`  | Ícone em PNG      |

O atalho é gerado com o Python **e** a pasta usados no momento do comando. Por isso:

- se você **mover a pasta do projeto**, rode o comando de novo;
- se usar um **venv**, rode com `.venv/bin/python main.py --install-desktop`, e o atalho
  passará a abrir o app com o Python do venv.

Para remover o atalho e os ícones:

```bash
python3 main.py --uninstall-desktop
```

## Onde ficam os seus dados

| Arquivo                                                  | Conteúdo                                    |
|----------------------------------------------------------|---------------------------------------------|
| `~/.config/discord-rpc-injector/presets.json`            | Predefinições salvas                        |
| `~/.config/DiscordRPCInjector/DiscordRPCInjector.conf`   | Preferências (tema, bandeja, último App ID) |

Ambos respeitam `XDG_CONFIG_HOME`. Para começar do zero, basta apagar esses arquivos.

---

Próximo: [Primeiros passos](02-primeiros-passos.md)
