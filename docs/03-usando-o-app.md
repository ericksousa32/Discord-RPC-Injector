# 3. Using the app

> **Summary:** four pages in the sidebar; the top bar shows the page title, the search
> (when there is one) and the action buttons of the current page.

```
┌──────────────┬──────────────────────────────────────────────────────┐
│ ▣ Discord RPC│ Page title                [search]     [page actions] │
│              ├──────────────────────────────────────────────────────┤
│ ● Presence   │                                                      │
│ ★ Presets    │                    page content                      │
│ ⟲ Log        │                                                      │
│ ⚙ Settings   │                                       ┌────────────┐ │
│              │                                       │notification│ │
│ ○ Disconnect │                                       └────────────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
```

The badge at the bottom of the sidebar shows the connection state on any page.

## Presence

The main editor, described in detail in [Getting started](02-primeiros-passos.md).

- **Actions:** Save preset · Clear · Apply.
- **Subtitle:** shows the state, such as "Not connected", "Ready to apply",
  "Presence active on Discord" or **"Unapplied changes"** (when you edit the fields after
  applying).
- **Validation:** before sending, the app checks the buttons (label and URL together; URL
  starting with `http://` or `https://`) and the group (numbers, with max ≥ size). Fields
  with a problem get a red border.

### Choosing a preset from the Application ID field

Click the **Application ID** field (or press **↓** in it) to see the list of saved presets,
with name, App ID and texts.

- Type part of an App ID to filter.
- Click an item, or use **↑/↓** + **Enter**, to load all of its fields.
- **Enter** with no item selected still means "Connect".
- While the connection is open the field is locked. To change the App ID, disconnect first.

## Presets

A list of everything you saved. The number next to the item in the sidebar is the total.

<!-- Alt text (kept for when the screenshot returns): Página Predefinições -->
> 📷 Screenshot coming soon.

| Action                  | What it does                                                   |
|-------------------------|----------------------------------------------------------------|
| New from current        | Saves the fields of the Presence page with a name              |
| Rename                  | Changes the name (does not allow a name that already exists)   |
| Delete                  | Asks for confirmation; the notification offers **Undo** for 7 s |
| Load                    | Fills in the Presence page (double-click also works)           |

The **search** looks in the name, the texts and the App ID. Use several words to narrow it down.

## Log

The session history: connections, sends, errors and presets used.

- **Search** filters by the text of the message.
- The level selector shows only success, warnings, errors or information.
- **Clear log** erases the history (it is not saved to disk).

## Settings

- **Appearance:**
  - **System** follows the colours and accent colour of KDE Plasma (read from
    `~/.config/kdeglobals`) and updates on its own when you change the Plasma theme.
    In other environments it uses the Qt palette.
  - **Light** and **Dark** fix the theme.

  <!-- Alt text (kept for when the screenshot returns): Página Presença no tema claro -->
  > 📷 Screenshot coming soon.

- **Behaviour:** "Keep in the system tray when the window is closed". If no tray is available
  (common on GNOME without an extension), the option is disabled and closing the window quits
  the app.
- **About:** version and location of the presets file.
- **Language (being added):** a selector with English and Brazilian Portuguese.

## Notifications

They appear in the bottom-right corner and disappear on their own. Hovering the mouse over
them pauses the timer. Errors stay visible longer.

## Keyboard shortcuts

| Shortcut      | Action                                                         |
|---------------|----------------------------------------------------------------|
| Ctrl+1        | Presence page                                                  |
| Ctrl+2        | Presets page                                                   |
| Ctrl+3        | Log page                                                       |
| Ctrl+,        | Settings page                                                  |
| Ctrl+F        | Search (goes to Presets if the current page has no search)     |
| Ctrl+S        | Save the current fields as a preset                            |
| Ctrl+Enter    | Apply the presence                                             |
| Ctrl+Q        | Quit the app (even with the tray enabled)                      |
| ↓ (in App ID) | Open the preset list                                           |

## System tray

With the tray enabled, closing the window **does not quit** the app: it keeps running and the
presence stays on Discord. Click the tray icon to reopen the window, or use its menu
(**Open** / **Quit**). When you quit, the presence is removed.

---

Previous: [Getting started](02-primeiros-passos.md) · Next: [How it works](04-como-funciona.md)
