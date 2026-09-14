# Insta Music Downloader

🇷🇺 [Читать на русском](README.md)

Paste a link (or several) to an Instagram Reel, pick a folder — get the MP3
audio track of the post. It's essentially a GUI wrapper around `yt-dlp -x
--audio-format mp3` with a modern interface, and it doesn't require
installing Python, ffmpeg, or anything else — just unzip and run the `.exe`.

Why: Instagram doesn't let you download audio from Reels directly, and
running `yt-dlp` from the console every time is tedious. This is a small
local tool with a two-click flow: link → folder → finished MP3.

## Screenshots

| Light theme | Dark theme, multiple links |
| --- | --- |
| ![Light theme](docs/screenshots/light-theme.png) | ![Dark theme](docs/screenshots/dark-theme.png) |

## Features

- Fluent Design UI (PySide6 + QFluentWidgets) with a Mica backdrop and a
  one-click light/dark theme toggle.
- Multiple links at once: each has its own card with a status pill and a
  "Download" button, plus a shared "Download all" button.
- Per-download status indicator (queued / downloading / done / error) with
  a live progress percentage.
- Remembers the last save folder and pre-fills it on the next launch.
- Filename is generated automatically from the post title.
- Animated splash screen on startup.
- Ships as a portable folder with a `.exe` — ffmpeg and yt-dlp are bundled
  inside, nothing else needs to be installed on the target machine.

## Download a pre-built copy

You don't have to build it yourself — the
[Releases](https://github.com/xQula/insta-music-downloader/releases) page
has a ready-made archive: unzip it and run
`InstaMusicDownloader\InstaMusicDownloader.exe`.

## Running from source (development)

```powershell
pip install -r requirements.txt
python scripts\fetch_ffmpeg.py   # once — downloads ffmpeg.exe into vendor\ffmpeg
python -m app.main
```

## Building the .exe

```powershell
.\scripts\build.cmd
```

(`build.cmd` is a wrapper around `build.ps1` that runs PowerShell with
`-ExecutionPolicy Bypass`; it's needed because on some machines running
`.ps1` scripts is disabled by default security policy. If scripts are
allowed on your machine, you can call `.\scripts\build.ps1` directly.)

The build script creates an isolated `.venv` and installs only the
dependencies from `requirements.txt` into it — this keeps PyInstaller from
sweeping unrelated packages that might be installed in your system Python
into the exe.

Build output: the `dist\InstaMusicDownloader\` folder (an `--onedir`
build) — copy and move it as a whole, and run
`dist\InstaMusicDownloader\InstaMusicDownloader.exe` from inside it. This
way the app starts almost instantly and can show an animated loading
screen (no unpacking to a temp folder, unlike `--onefile`).

## macOS

Apple Silicon (arm64) builds are supported, macOS 12+. A pre-built archive
(once one exists) lives on the same
[Releases](https://github.com/xQula/insta-music-downloader/releases) page —
it ships with a first-launch instructions file right next to the `.app`.

The app isn't signed with an Apple Developer ID (a paid subscription), so a
normal double-click will make macOS show "Apple could not verify that this
app is free of malware". The simplest way to open it:

1. Double-click the `.app` — the warning appears. Dismiss it.
2. Open **System Settings → Privacy & Security**.
3. Scroll down to the "Security" section — it will show a message that the
   app was blocked, with an **"Open Anyway"** button next to it.
4. Click it, then confirm in the dialog. You only need to do this once, on
   first launch.

To build it yourself (requires [Homebrew](https://brew.sh)):

```bash
./scripts/build_macos.sh
```

The script creates its own `.venv`, installs ffmpeg via Homebrew, and
produces `dist/InstaMusicDownloader.app`. The build is actually exercised in
CI — see `.github/workflows/build-macos.yml` (runs on pushing a `v*` tag, or
manually from the Actions tab).

## Where settings are stored

The last selected folder is saved to
`%APPDATA%\InstaMusicDownloader\config.json` on Windows, and to
`~/Library/Application Support/InstaMusicDownloader/config.json` on macOS.

## Limitations

- Downloads are anonymous, without logging into an account — private posts
  aren't accessible.
- yt-dlp is baked into the exe at build time. Instagram periodically
  changes its internal API — if downloading stops working, update the
  dependency and rebuild the exe:
  ```powershell
  pip install -U yt-dlp
  .\scripts\build.cmd
  ```

## License

[MIT](LICENSE)
