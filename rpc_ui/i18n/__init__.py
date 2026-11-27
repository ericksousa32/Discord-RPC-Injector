"""Textos da interface: ``tr(chave, **valores)`` devolve a mensagem do catálogo.

As chaves são estáveis (``área.assunto``), e o código nunca depende do texto
exibido. Valores dinâmicos entram como ``{nome}`` no catálogo.
"""

from __future__ import annotations

from .catalog import MESSAGES


def tr(key: str, **values) -> str:
    text = MESSAGES.get(key, key)
    return text.format(**values) if values else text
