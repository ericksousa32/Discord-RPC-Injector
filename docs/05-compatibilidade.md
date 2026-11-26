# 5. Compatibilidade

> **Resumo:** funciona com o Discord nativo, Flatpak e Snap, em distros baseadas no Fedora
> e no Ubuntu, sem `sudo` e sem configuração manual de sockets.

## Instalações do Discord

| Instalação                              | Suporte | Observação                                           |
|-----------------------------------------|:-------:|------------------------------------------------------|
| Nativo: rpm, deb, tar.gz                | ✅      | Socket em `$XDG_RUNTIME_DIR`                          |
| PTB / Canary nativos (2ª instância)     | ✅      | `discord-ipc-1` … `-9`                                |
| Flatpak `com.discordapp.Discord`        | ✅      | Usa o socket criado pelo lançador do Flathub          |
| Flatpak `com.discordapp.DiscordCanary`  | ✅      |                                                      |
| Flatpak Vesktop `dev.vencord.Vesktop`   | ✅*     | Depende do servidor RPC (arRPC) estar ativo no Vesktop |
| Snap `discord`                          | ✅      | Socket em `snap.discord/`                             |
| Discord no navegador                    | ❌      | O navegador não abre socket IPC                       |

\* Coberto pelos testes automatizados com um Discord simulado, mas não verificado com o
Vesktop real.

> ℹ️ O comportamento com o **Discord Flatpak** foi verificado com o Discord real. Os demais
> formatos são cobertos por testes automatizados que simulam o socket exatamente onde cada
> instalação o cria (veja [Desenvolvimento](08-desenvolvimento.md#rodando-os-testes)).

## Distribuições

| Família             | Motor | Interface                                                    |
|---------------------|:-----:|--------------------------------------------------------------|
| Fedora e derivadas  | ✅    | `python3-pyside6` dos repositórios                           |
| Ubuntu / Debian     | ✅    | `python3-pyside6.*` se for 6.5 ou mais novo; senão, venv + pip |
| Outras (Arch, openSUSE…) | ✅ | Pacote PySide6 da distro ou venv + pip                    |

O **motor** usa só a biblioteca padrão do Python 3.8+, então roda em qualquer distro.
A **interface** precisa do PySide6 6.5 ou mais novo. Veja [Instalação](01-instalacao.md).

## Ambientes de desktop

| Recurso                        | KDE Plasma              | GNOME                           | Outros                  |
|--------------------------------|-------------------------|---------------------------------|-------------------------|
| Tema "Sistema"                 | Cores e destaque do KDE | Paleta e modo claro/escuro do Qt| Paleta do Qt            |
| Bandeja do sistema             | ✅                      | Só com extensão AppIndicator     | Depende do painel       |
| Ícone na barra (Wayland)       | ✅ com o atalho instalado | ✅ com o atalho instalado      | ✅ com o atalho instalado |

Sem bandeja disponível, fechar a janela simplesmente encerra o app.

## Permissões: precisa de sudo?

**Não.** Tudo o que o app lê ou escreve pertence ao seu usuário:

| Recurso                     | Local                                         | Dono          |
|-----------------------------|-----------------------------------------------|---------------|
| Socket do Discord           | `/run/user/<uid>/…`                           | você          |
| Predefinições               | `~/.config/discord-rpc-injector/`             | você          |
| Preferências                | `~/.config/DiscordRPCInjector/`               | você          |
| Atalho e ícone              | `~/.local/share/…`                            | você          |

> ⚠️ **Não rode o app com `sudo`.** Como root, ele procuraria o socket na pasta do root
> (`/run/user/0`) e não encontraria o Discord do seu usuário.

O SELinux (Fedora) e o AppArmor (Ubuntu) não bloqueiam a conexão: o app roda fora de
sandbox, com as mesmas permissões que você.

## Se o próprio app for empacotado como Flatpak

Hoje o app roda direto no sistema. Se um dia for empacotado como Flatpak, ele precisará de
permissão para enxergar o socket do Discord, por exemplo
`--filesystem=xdg-run/app/com.discordapp.Discord:ro` e `--filesystem=xdg-run/discord-ipc-0:ro`.

---

Anterior: [Como funciona](04-como-funciona.md) · Próximo: [Solução de problemas](06-solucao-de-problemas.md)
