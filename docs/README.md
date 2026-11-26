# Documentação do Discord RPC Injector

Bem-vindo! Esta pasta reúne tudo o que você precisa para **usar**, **entender** e
**modificar** o Discord RPC Injector. Cada arquivo trata de um assunto só e pode ser lido
de forma independente.

## Por onde começar?

| Eu quero…                                         | Leia                                                  |
|---------------------------------------------------|-------------------------------------------------------|
| Instalar e abrir o app                            | [Instalação](01-instalacao.md)                        |
| Mostrar minha primeira presença no Discord        | [Primeiros passos](02-primeiros-passos.md)            |
| Conhecer cada tela, atalho e opção                | [Usando o app](03-usando-o-app.md)                    |
| Entender como o app conversa com o Discord        | [Como funciona](04-como-funciona.md)                  |
| Saber se funciona na minha distro/instalação      | [Compatibilidade](05-compatibilidade.md)              |
| Resolver um problema                              | [Solução de problemas](06-solucao-de-problemas.md)    |
| Entender como o código está organizado            | [Arquitetura](07-arquitetura.md)                      |
| Rodar os testes ou contribuir com código          | [Desenvolvimento](08-desenvolvimento.md)              |
| Usar o motor em outro script Python               | [Referência do motor](09-referencia-do-motor.md)      |

## Os módulos

**Para quem usa**

1. [Instalação](01-instalacao.md): dependências no Fedora, Ubuntu ou venv e atalho no menu.
2. [Primeiros passos](02-primeiros-passos.md): do Developer Portal até a presença aparecer no perfil.
3. [Usando o app](03-usando-o-app.md): páginas, predefinições, atalhos de teclado, tema e bandeja.

**Para quem quer entender**

4. [Como funciona](04-como-funciona.md): o socket IPC do Discord explicado sem complicação.
5. [Compatibilidade](05-compatibilidade.md): Discord nativo, Flatpak e Snap; Fedora e Ubuntu; sem sudo.
6. [Solução de problemas](06-solucao-de-problemas.md): sintomas comuns e como resolver.

**Para quem desenvolve**

7. [Arquitetura](07-arquitetura.md): camadas, pastas e fluxo de dados.
8. [Desenvolvimento](08-desenvolvimento.md): testes, criação de páginas e widgets, tema.
9. [Referência do motor](09-referencia-do-motor.md): API do `discord_rpc_injector.py`.

## Glossário rápido

- **Rich Presence (RPC):** o cartão "Jogando…" que aparece no seu perfil do Discord.
- **Application ID:** número que identifica o "aplicativo" criado no Discord Developer Portal.
  O nome desse aplicativo é o que aparece em "Jogando **…**".
- **Socket IPC:** arquivo especial (`discord-ipc-0`) pelo qual programas locais conversam
  com o Discord aberto no seu computador.
- **Predefinição:** um conjunto de campos salvo com um nome, para reutilizar depois.
- **Motor:** o arquivo `discord_rpc_injector.py`, que fala com o Discord. A interface gráfica
  fica no pacote `rpc_ui/`.
