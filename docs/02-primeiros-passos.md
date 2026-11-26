# 2. Primeiros passos

> **Resumo:** crie um aplicativo no Discord Developer Portal, copie o **Application ID**,
> cole no app, clique em **Conectar** e depois em **Aplicar**.

## Passo 1: criar um "aplicativo" no Discord

O Discord só mostra presenças ligadas a um aplicativo registrado. O nome desse aplicativo é
o que aparece em **"Jogando …"** no seu perfil.

1. Acesse <https://discord.com/developers/applications> e faça login.
2. Clique em **New Application** e dê o nome que deve aparecer no perfil (ex.: `Fedora`).
3. Na página do aplicativo, copie o **Application ID** (um número longo).

### Opcional: imagens

1. No mesmo aplicativo, abra **Rich Presence → Art Assets**.
2. Envie as imagens. O **nome** de cada uma vira a **chave** usada no app (ex.: `logo`).

> 💡 Imagens recém-enviadas podem levar alguns minutos para ficarem disponíveis.

## Passo 2: conectar

1. Deixe o **Discord aberto** (nativo, Flatpak ou Snap).
2. Abra o Discord RPC Injector, na página **Presença**.
3. No card **Conexão**, cole o Application ID e clique em **Conectar** (ou tecle Enter).
4. O selo muda para **● Conectado** e o caminho do socket encontrado aparece abaixo do campo.

## Passo 3: montar e aplicar a presença

Preencha o que quiser. Todos os campos são opcionais.

| Card          | Campo                  | Onde aparece no Discord                         |
|---------------|------------------------|-------------------------------------------------|
| Texto         | Detalhes               | 1ª linha abaixo do nome do aplicativo           |
| Texto         | Estado                 | 2ª linha                                        |
| Texto         | Mostrar tempo decorrido| "00:12 decorrido"                               |
| Imagens       | Grande / Pequena       | Chave do Art Asset                              |
| Imagens       | Dica                   | Texto ao passar o mouse sobre a imagem          |
| Botões        | Rótulo + URL           | Até 2 botões com links (`http://` ou `https://`)|
| Grupo (party) | Tamanho / Máximo       | "(2 de 4)" ao lado do estado                    |

A **pré-visualização** à direita mostra uma aproximação do cartão enquanto você digita.

Clique em **Aplicar** (ou **Ctrl+Enter**). Pronto: a presença aparece no seu perfil.

> 💡 O Discord costuma **não mostrar os botões para você mesmo**. Peça para alguém conferir
> o seu perfil.

## Passo 4: salvar para usar depois

Clique em **Salvar predefinição** (ou **Ctrl+S**) e dê um nome. Na próxima vez, basta clicar
no campo **Application ID** e escolher a predefinição na lista. Veja
[Usando o app → Predefinições](03-usando-o-app.md#predefinições).

## Para remover a presença

- **Limpar** remove a presença e mantém a conexão aberta.
- **Desconectar** fecha a conexão. Ao sair do app, a presença também é removida.

---

Anterior: [Instalação](01-instalacao.md) · Próximo: [Usando o app](03-usando-o-app.md)
