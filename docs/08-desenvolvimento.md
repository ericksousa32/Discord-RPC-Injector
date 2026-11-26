# 8. Desenvolvimento

> **Resumo:** `python3 -m unittest discover -s tests -t .` roda todos os testes sem abrir
> janelas e sem precisar do Discord. Novas telas são uma classe `Page`; novos componentes
> vão para `widgets/`; cores vêm sempre dos tokens do tema.

## Rodando os testes

Na pasta do projeto:

```bash
python3 -m unittest discover -s tests -t .
```

Para ver o nome de cada teste, adicione `-v`. Para rodar um arquivo só:

```bash
python3 -m unittest tests.test_engine -v
```

Os testes:

- usam o Qt em modo **offscreen** (nenhuma janela aparece);
- **não** conectam ao Discord real: usam um IPC falso ou um servidor que imita o Discord;
- **não** tocam nos seus arquivos: predefinições ficam em memória ou em pastas temporárias.

### O que cada arquivo cobre

| Arquivo                | Cobre                                                                 |
|------------------------|-----------------------------------------------------------------------|
| `test_startup.py`      | Janela abre, página inicial, estado desconectado, tema KDE/claro/escuro |
| `test_navigation.py`   | Barra lateral, barra superior, busca por página, atalhos              |
| `test_interaction.py`  | Conectar, aplicar, limpar, validação, predefinições (salvar, renomear, excluir/desfazer), lista no campo App ID, registro, diálogos, notificações, formato do payload |
| `test_engine.py`       | Socket de cada tipo de instalação, tempos limite, recusa, socket abandonado, protocolo, gravação de predefinições, atalho `.desktop` |

### Ferramentas de teste (`tests/helpers.py`)

| Ferramenta        | Para quê                                                          |
|-------------------|-------------------------------------------------------------------|
| `AppTestCase`     | Cria uma janela isolada por teste (presets em memória, settings temporário, `kdeglobals` falso) |
| `FakeIPC`         | Substitui `DiscordIPC`; registra o que foi enviado; pode simular falhas (`fail_connect`, `fail_send`) |
| `ScriptedDialogs` | Responde aos diálogos com valores pré-definidos (`texts`, `confirms`) |
| `sync_runner`     | Executa o "segundo plano" do controlador na hora, deixando o teste determinístico |

Em `test_engine.py`, a classe `FakeDiscord` abre um socket Unix de verdade e se comporta
como o Discord nos modos `ready`, `delay`, `reject` e `silent`.

### Exemplo de teste de interface

```python
from tests.helpers import AppTestCase, FakeIPC

class MeuTeste(AppTestCase):
    def test_aplicar_envia_detalhes(self):
        self.connect()                                   # conecta com o FakeIPC
        self.presence.fields["details"].setText("Codando")
        self.presence.btn_apply.click()
        self.assertEqual(FakeIPC.instances[0].sent[-1]["details"], "Codando")
```

## Como adicionar uma página

1. Crie `rpc_ui/pages/minha_pagina.py`:

   ```python
   from .base import Page
   from ..widgets import Button, Card

   class MinhaPagina(Page):
       key = "minha"
       title = "Minha página"
       icon = "help-about"                 # nome de ícone freedesktop
       search_placeholder = None           # ou "Buscar…" para ativar a busca

       def __init__(self, ctx, parent=None):
           super().__init__(parent)
           self.ctx = ctx
           self.btn = Button("Fazer algo", "dialog-ok", "primary", on_click=self.fazer)
           # ... monte o layout com Card, FormGrid etc.

       def subtitle(self):
           return "Descrição curta"

       def header_actions(self):
           return [self.btn]

       def fazer(self):
           self.ctx.notify("Feito!", tone="ok")
   ```

2. Exporte em `rpc_ui/pages/__init__.py`.
3. Registre em `MainWindow.__init__` com `self._add_page(MinhaPagina(ctx), "Ctrl+4")`.
4. Adicione um caso em `tests/test_navigation.py`.

## Como adicionar um widget

- Coloque em `rpc_ui/widgets/` e exporte em `widgets/__init__.py`.
- **Sem lógica de negócio**: o widget recebe dados e emite sinais.
- **Sem cores fixas**: defina um `objectName` (ou a propriedade `variant` com `set_prop`) e
  adicione as regras em `theme/stylesheet.py` usando os tokens.

## Como mexer no tema

- Cores novas: adicione o campo em `Tokens` (`theme/palette.py`), preencha em `LIGHT`,
  `DARK` e em `_from_colors` (modo Sistema).
- Estilos: edite `build_stylesheet()` em `theme/stylesheet.py`.
- Ícones: `widgets/icons.py` usa o tema de ícones do sistema (Breeze no KDE) e desenha um
  símbolo simples quando o ícone não existe.

## Convenções

- Textos da interface e documentação em **português**.
- Cada arquivo com uma responsabilidade; páginas não importam o motor diretamente (use o
  `AppContext`).
- Operações de rede sempre pelo `PresenceController` (nunca na thread da interface).
- Todo comportamento novo vem com um teste.

## Gerando capturas de tela sem abrir janelas

```python
import os; os.environ["QT_QPA_PLATFORM"] = "offscreen"
from rpc_ui.app import create_app, build_window

app = create_app([])
win = build_window(app, enable_tray=False)
win.resize(1180, 760); win.show(); app.processEvents()
win.grab().save("captura.png")
```

---

Anterior: [Arquitetura](07-arquitetura.md) · Próximo: [Referência do motor](09-referencia-do-motor.md)
