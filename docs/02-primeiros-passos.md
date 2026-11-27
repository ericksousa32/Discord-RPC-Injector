# 2. Getting started

> **Summary:** create an application in the Discord Developer Portal, copy the
> **Application ID**, paste it into the app, click **Connect** and then **Apply**.

## Step 1: create an "application" in Discord

Discord only shows presence tied to a registered application. The name of that application
is what appears under **"Playing …"** on your profile.

1. Go to <https://discord.com/developers/applications> and log in.
2. Click **New Application** and give it the name that should appear on your profile
   (e.g. `Fedora`).
3. On the application page, copy the **Application ID** (a long number).

### Optional: images

1. In the same application, open **Rich Presence → Art Assets**.
2. Upload the images. The **name** of each one becomes the **key** used in the app
   (e.g. `logo`).

> 💡 Newly uploaded images can take a few minutes to become available.

## Step 2: connect

1. Leave the **Discord open** (native, Flatpak or Snap).
2. Open Discord RPC Injector, on the **Presence** page.
3. In the **Connection** card, paste the Application ID and click **Connect** (or press Enter).
4. The badge changes to **● Connected** and the socket path that was found appears below
   the field.

## Step 3: build and apply the presence

Fill in whatever you want. All fields are optional.

| Card          | Field                  | Where it appears in Discord                       |
|---------------|------------------------|---------------------------------------------------|
| Text          | Details                | 1st line below the application name               |
| Text          | State                  | 2nd line                                          |
| Text          | Show elapsed time      | "00:12 elapsed"                                   |
| Images        | Large / Small          | Art Asset key                                     |
| Images        | Tooltip                | Text shown when hovering over the image           |
| Buttons       | Label + URL            | Up to 2 buttons with links (`http://` or `https://`) |
| Group (party) | Size / Max             | "(2 of 4)" next to the state                      |

The **preview** on the right shows an approximation of the card while you type.

Click **Apply** (or **Ctrl+Enter**). Done: the presence shows on your profile.

> 💡 Discord usually **does not show the buttons to yourself**. Ask someone to check your
> profile.

## Step 4: save it for later

Click **Save preset** (or **Ctrl+S**) and give it a name. Next time, click the
**Application ID** field and pick the preset from the list. See
[Using the app → Presets](03-usando-o-app.md#presets).

## To remove the presence

- **Clear** removes the presence and keeps the connection open.
- **Disconnect** closes the connection. When you quit the app, the presence is removed too.

---

Previous: [Installation](01-instalacao.md) · Next: [Using the app](03-usando-o-app.md)
