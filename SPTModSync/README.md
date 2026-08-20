# SPT Mod Sync

SPT/EFT mod sharing between peers — no browser. Publish patches, receive updates from your buddy (or yourself) and keep everything synced over LAN or VPN (Radmin).

Partilha de mods SPT/EFT entre peers — sem browser. Publica patches, recebe updates do teu colega (ou de ti próprio) e mantém tudo sincronizado via LAN ou VPN (Radmin).

## Features / Funcionalidades

- **Publish / Publicar** — select files, make a patch (zip), then send it to a server.
- **Update / Actualizar** — receive patches: download, remove obsolete files, extract into SPT folder.
- **Embedded Flask server / Servidor Flask embutido** — runs inside the app, no extra window.
- **i18n PT-PT / EN** — full UI translation, external `Data/Lang/*.json`.
- **Auto-update / Auto-atualização** — checks GitHub Releases for new versions.

## Build / Compilar

```
pyinstaller SPTModSync.spec
```

The spec bundles `index.html`, `assets/` and `Data/Server/server.py`. External editable data (`Data/Lang`, `Data/Logs`, `Data/Patches`) lives next to the exe at runtime.

## Version / Versão

v0.5 - Beta
