"""Gera a folha de estilo (QSS) da aplicação a partir dos tokens.

Os widgets reutilizáveis usam ``objectName`` ou a propriedade dinâmica
``variant`` para escolher o estilo, sem cores fixas espalhadas no código.
"""

from __future__ import annotations

from .palette import Tokens

RADIUS = 8


def build_stylesheet(t: Tokens) -> str:
    r = RADIUS
    return f"""
* {{ outline: none; }}
QMainWindow, QDialog, #AppRoot {{ background: {t.window}; color: {t.text}; }}
QWidget {{ color: {t.text}; }}
QToolTip {{ background: {t.surface}; color: {t.text}; border: 1px solid {t.border};
            padding: 4px 8px; border-radius: 6px; }}

/* ── Sidebar ───────────────────────────────────────────── */
#Sidebar {{ background: {t.sidebar}; border-right: 1px solid {t.border}; }}
#SidebarTitle {{ font-weight: 600; font-size: 11pt; }}
#SidebarSubtitle, #SidebarSection {{ color: {t.text_faint}; font-size: 8pt; }}
#SidebarSection {{ font-weight: 600; letter-spacing: 1px; }}
QPushButton#NavItem {{
    text-align: left; padding: 8px 12px; border: none; border-radius: {r}px;
    background: transparent; color: {t.text_muted}; font-size: 10pt;
}}
QPushButton#NavItem:hover {{ background: {t.hover}; color: {t.text}; }}
QPushButton#NavItem:checked {{ background: {t.accent_soft(56)}; color: {t.text}; font-weight: 600; }}
#NavBadge {{ background: {t.surface_alt}; color: {t.text_muted}; border-radius: 9px;
             padding: 1px 7px; font-size: 8pt; }}

/* ── Header ────────────────────────────────────────────── */
#PageHeader {{ background: {t.window}; border-bottom: 1px solid {t.border}; }}
#PageTitle {{ font-size: 15pt; font-weight: 600; }}
#PageSubtitle {{ color: {t.text_muted}; }}

/* ── Inputs ────────────────────────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{
    background: {t.surface_alt}; border: 1px solid {t.border}; border-radius: 6px;
    padding: 6px 9px; selection-background-color: {t.accent}; selection-color: {t.on_accent};
}}
QLineEdit:hover, QComboBox:hover {{ border-color: {t.text_faint}; }}
QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {t.accent}; }}
QLineEdit:disabled {{ color: {t.text_faint}; }}
QLineEdit[invalid="true"] {{ border: 1px solid {t.danger}; }}
QLineEdit#SearchField {{ border-radius: 16px; padding: 6px 12px; min-width: 220px; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {t.surface}; border: 1px solid {t.border};
    selection-background-color: {t.accent_soft(70)}; selection-color: {t.text}; }}

/* ── Buttons ───────────────────────────────────────────── */
QPushButton {{
    background: {t.surface}; border: 1px solid {t.border}; border-radius: 6px;
    padding: 6px 14px; color: {t.text};
}}
QPushButton:hover {{ background: {t.hover}; }}
QPushButton:pressed {{ background: {t.border}; }}
QPushButton:disabled {{ color: {t.text_faint}; background: {t.surface_alt}; border-color: {t.surface_alt}; }}
QPushButton[variant="primary"] {{ background: {t.accent}; border-color: {t.accent}; color: {t.on_accent}; font-weight: 600; }}
QPushButton[variant="primary"]:hover {{ background: {t.tint(t.accent, 225)}; }}
QPushButton[variant="primary"]:disabled {{ background: {t.accent_soft(60)}; border-color: transparent; color: {t.text_faint}; }}
QPushButton[variant="danger"] {{ color: {t.danger}; }}
QPushButton[variant="danger"]:hover {{ background: {t.tint(t.danger, 36)}; border-color: {t.danger}; }}
QPushButton[variant="flat"] {{ background: transparent; border-color: transparent; }}
QPushButton[variant="flat"]:hover {{ background: {t.hover}; }}
QPushButton[variant="flat"]:disabled {{ background: transparent; }}

/* ── Cards / sections ──────────────────────────────────── */
#Card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {r + 2}px; }}
#CardTitle {{ font-weight: 600; font-size: 10.5pt; }}
#CardSubtitle, #FieldHint {{ color: {t.text_muted}; font-size: 9pt; }}
#FieldLabel {{ color: {t.text_muted}; }}
#Separator {{ background: {t.border}; max-height: 1px; min-height: 1px; }}

/* ── Status pill ───────────────────────────────────────── */
#StatusPill {{ border-radius: 11px; padding: 3px 10px; font-size: 9pt; font-weight: 600; }}
#StatusPill[tone="ok"] {{ background: {t.tint(t.success, 40)}; color: {t.success}; }}
#StatusPill[tone="busy"] {{ background: {t.tint(t.warning, 40)}; color: {t.warning}; }}
#StatusPill[tone="off"] {{ background: {t.surface_alt}; color: {t.text_muted}; }}

/* ── Empty state ───────────────────────────────────────── */
#EmptyTitle {{ font-size: 13pt; font-weight: 600; }}
#EmptyText {{ color: {t.text_muted}; }}

/* ── Lists ─────────────────────────────────────────────── */
QListWidget, QListView {{ background: transparent; border: none; }}
QListWidget::item {{ border-radius: {r}px; padding: 0; margin: 2px 0; }}
QListWidget::item:selected {{ background: {t.accent_soft(56)}; color: {t.text}; }}
QListWidget::item:hover:!selected {{ background: {t.hover}; }}
QListView#SuggestionPopup {{ background: {t.surface}; border: 1px solid {t.border}; padding: 0; }}
#PresetRowTitle {{ font-weight: 600; }}
#PresetRowMeta {{ color: {t.text_muted}; font-size: 9pt; }}
#LogTime {{ color: {t.text_faint}; font-family: monospace; }}
#LogMessage {{ font-family: monospace; }}

/* ── Preview (cartão de atividade) ─────────────────────── */
#PreviewCard {{ background: {t.surface_alt}; border-radius: {r + 2}px; border: 1px solid {t.border}; }}
#PreviewHeading {{ color: {t.text_muted}; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }}
#PreviewApp {{ font-weight: 600; }}
#PreviewLine {{ color: {t.text_muted}; }}
#PreviewImage {{ background: {t.accent_soft(70)}; border-radius: 10px; color: {t.text}; font-weight: 700; }}
#PreviewSmallImage {{ background: {t.surface}; border: 2px solid {t.surface_alt}; border-radius: 11px; }}
QPushButton#PreviewButton {{ background: {t.hover}; border: none; }}

/* ── Toasts ────────────────────────────────────────────── */
#Toast {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {r + 2}px; }}
#Toast[tone="ok"] {{ border-left: 4px solid {t.success}; }}
#Toast[tone="err"] {{ border-left: 4px solid {t.danger}; }}
#Toast[tone="warn"] {{ border-left: 4px solid {t.warning}; }}
#Toast[tone="info"] {{ border-left: 4px solid {t.accent}; }}
#ToastTitle {{ font-weight: 600; }}
#ToastText {{ color: {t.text_muted}; }}

/* ── Dialogs ───────────────────────────────────────────── */
#DialogTitle {{ font-size: 12pt; font-weight: 600; }}
#DialogText {{ color: {t.text_muted}; }}
#DialogError {{ color: {t.danger}; font-size: 9pt; }}

/* ── Radio “segmented” (tema) ──────────────────────────── */
QRadioButton#ThemeOption {{ background: {t.surface_alt}; border: 1px solid {t.border}; border-radius: {r}px;
    padding: 10px 14px; }}
QRadioButton#ThemeOption:checked {{ border: 2px solid {t.accent}; background: {t.accent_soft(30)}; }}

/* ── Scrollbars ────────────────────────────────────────── */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t.border}; border-radius: 3px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t.text_faint}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ background: none; height: 0; }}
QCheckBox {{ spacing: 8px; }}
"""
