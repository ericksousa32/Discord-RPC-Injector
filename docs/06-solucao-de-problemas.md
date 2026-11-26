# 6. Solução de problemas

> **Dica geral:** a página **Registro** mostra cada passo da conexão e a mensagem de erro
> completa. Comece por ela.

## "Socket do Discord não encontrado"

O app não achou nenhum `discord-ipc-*` nos lugares conhecidos.

1. O Discord está **aberto e logado**? (Não basta estar no navegador.)
2. Liste os sockets existentes:

   ```bash
   find "$XDG_RUNTIME_DIR" /tmp -maxdepth 4 -name 'discord-ipc-*' 2>/dev/null
   ```

3. Se o comando não mostrar nada, feche o Discord **por completo** (inclusive pela bandeja)
   e abra de novo.
4. Se o socket estiver num lugar fora da lista de
   [Como funciona](04-como-funciona.md#1-encontrar-o-socket), abra uma issue informando o
   caminho.

## "O Discord recusou a conexão: Invalid Client ID (código 4000)"

O Application ID não existe ou foi digitado errado. Copie de novo em
<https://discord.com/developers/applications> → seu aplicativo → **Application ID**.

## "O Discord não respondeu em 12 s" ou demora para conectar

O Discord às vezes segura novas conexões por alguns segundos, principalmente depois de
conectar e desconectar várias vezes seguidas.

- Espere uns 10 segundos e clique em **Conectar** de novo.
- Se acontecer sempre, reinicie o Discord.

## Conecta, mas a presença não aparece

- Confira as **configurações do Discord**: *Atividade → Privacidade de atividade →*
  "Compartilhar sua atividade" precisa estar ligado.
- O status **Invisível** esconde a atividade.
- O Discord pode levar alguns segundos para atualizar o perfil.

## As imagens não aparecem

- A **chave** precisa ser exatamente o nome do asset em *Rich Presence → Art Assets*.
- Assets recém-enviados podem levar alguns minutos para ficarem disponíveis.

## Os botões não aparecem

O Discord costuma não mostrar os botões **para o próprio usuário**. Peça para alguém
conferir o seu perfil. Cada botão precisa de rótulo **e** URL (`http://` ou `https://`).

## Fechei a janela e o app continua rodando

É a opção **"Manter na bandeja do sistema ao fechar a janela"** (página Configurações).
Use **Ctrl+Q** ou **Sair** no menu da bandeja para encerrar de vez.

## O atalho do menu não abre o app

Provavelmente a pasta do projeto foi movida ou o Python mudou (ex.: novo venv). Gere o
atalho de novo:

```bash
python3 main.py --install-desktop
```

## "ModuleNotFoundError: No module named 'PySide6'" ou erro de versão do Qt

Instale ou atualize o PySide6 (precisa ser 6.5 ou mais novo). Veja
[Instalação](01-instalacao.md#instalando-as-dependências).

## O tema não segue o KDE

Em **Configurações → Aparência**, selecione **Sistema**. O app lê
`~/.config/kdeglobals`; se o arquivo não existir (fora do KDE), usa a paleta do Qt.

---

Anterior: [Compatibilidade](05-compatibilidade.md) · Próximo: [Arquitetura](07-arquitetura.md)
