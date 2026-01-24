# ES-DE SD Sync (NAS Master Cache → Per‑Device SD Card)

I use this tool to solve a repeating ES-DE problem: every new handheld/device needs scraping again. Instead, I scrape **once** into a **NAS master cache**, then this script:

- Writes a **filtered** `gamelist.xml` that contains **only** the ROMs on a given SD card
- Copies only the **media categories I choose** (covers, screenshots, marquees, etc.) from the NAS master cache to that SD card
- Provides a **non-destructive audit mode** to identify which ROMs are missing metadata/media in the master cache

This repo is optimized for **Windows 11** (PowerShell + `py`).

---

## Features ✅

- **One master scrape** → many SD cards / devices
- **System-aware** sync (`SD:\ROMs\<system>\...`)
- **Media profiles** (`profiles.json`) for “no_videos”, “everything”, etc.
- **Optional fuzzy matching** when filenames differ slightly
- **Audit mode** that reports:
  - ROMs missing from master `gamelist.xml` (missing metadata)
  - ROMs missing media in selected categories (missing artwork/videos)
- **Idempotent copies**: existing SD files with same size are skipped
- **Optional gamelist backup** before writing

---

## Repository Layout 📁

Recommended structure:

```
.
├─ sync_esde_sd.py
├─ profiles.json
├─ run_sync.ps1                      # optional interactive wrapper (PowerShell)
└─ docs
   ├─ ESDE_SD_Sync_All_Commands.md
   └─ ESDE_SD_Sync_Quick_Reference.md
```

- `docs/ESDE_SD_Sync_All_Commands.md` contains the exhaustive command list.
- `docs/ESDE_SD_Sync_Quick_Reference.md` is a one-page “most common commands” sheet.

---

## Requirements ✅

- **Windows 11**
- **Python**: I recommend Python 3.10+ (works with newer versions too)
  - Verify: `py --version`
- Network access to your NAS UNC path (example used throughout):
  - `\\10.42.42.2\media\retro_gaming\ES-DE_Master`

---

## Required Folder Structures ✅

### NAS Master Cache (authoritative source)

Master root contains:

- `\\...\ES-DE_Master\gamelists\<system>\gamelist.xml`
- `\\...\ES-DE_Master\downloaded_media\<system>\<category>\*`

Example categories:
`covers`, `screenshots`, `marquees`, `videos`, etc.

### SD Card (target)

SD root contains:

- `SD:\ROMs\<system>\...`
- `SD:\ES-DE\...`

Example:

- `F:\ROMs\switch\Celeste.xci`
- `F:\ES-DE\gamelists\switch\gamelist.xml`
- `F:\ES-DE\downloaded_media\switch\covers\Celeste.png`

---

## Installation / Setup 🛠️

1) Clone this repo:
   
   ```powershell
   git clone <your-repo-url>  # clone repository
   cd <repo-folder>           # enter repository
   ```

2) Ensure `profiles.json` exists (example):
   
   ```json
   {
   "artwork_only": ["covers","screenshots","titlescreens","marquees"],
   "no_videos": ["3dboxes","backcovers","covers","custom","fanart","manuals","marquees","miximages","physicalmedia","screenshots","titlescreens"],
   "everything": ["3dboxes","backcovers","covers","custom","fanart","manuals","marquees","miximages","physicalmedia","screenshots","titlescreens","videos"]
   }
   ```

3) Confirm your SD has `ROMs` and `ES-DE` at the root:
- If missing, create them:
  - `F:\ROMs\...`
  - `F:\ES-DE\...`

---

# Usage ✅

## A) Run in PowerShell (recommended)

### 1) Default sync (profile + backup)

**What it does**

- Filters gamelists to only ROMs on SD
- Copies media categories from profile
- Writes SD gamelist (backed up first)

```powershell
# Summary: sync using profile "no_videos" (recommended default)
py .\sync_esde_sd.py `                                                  # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `    # NAS master root
  --sd_root "F:" `                                                      # SD root
  --profile "no_videos" `                                               # media profile
  --backup_gamelist                                                     # backup SD gamelist.xml before writing
```

### 2) Same command (single line / no PowerShell line continuation)

```powershell
# Summary: same sync command as one line
py .\sync_esde_sd.py --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" --sd_root "F:" --profile "no_videos" --backup_gamelist  # one-liner
```

### 3) Audit first (recommended “new SD card” workflow)

**What it does**

- No copies, no writes
- Reports what is missing in your NAS master cache

```powershell
# Summary: audit SD ROMs vs master cache (no copies, no writes)
py .\sync_esde_sd.py `                                                  # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `    # NAS master root
  --sd_root "F:" `                                                      # SD root
  --profile "no_videos" `                                               # audit category selection
  --audit_missing_master                                                # audit-only mode
```

---

## B) Run WITHOUT PowerShell (Command Prompt / CMD)

Open **Command Prompt** in the repo folder and run:

```bat
:: Summary: sync using profile "no_videos" from CMD (single line)
py sync_esde_sd.py --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" --sd_root "F:" --profile "no_videos" --backup_gamelist
```

Audit from CMD:

```bat
:: Summary: audit mode from CMD (no copies, no writes)
py sync_esde_sd.py --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" --sd_root "F:" --profile "no_videos" --audit_missing_master
```

---

## C) Optional: Use the interactive wrapper (PowerShell) 🧰

If you include `run_sync.ps1`, it can:

- Detect candidate SD drives (looks for `\ROMs` + `\ES-DE`)
- Let you pick a drive + profile
- Build and run the Python command

Run it:

```powershell
# Summary: interactive wrapper (drive + profile picker)
.\run_sync.ps1  # prompts for SD drive/profile and executes sync
```

---

# Command Reference 📚

I keep two docs in `docs/`:

- `docs/ESDE_SD_Sync_All_Commands.md`  
  **Every** supported command combination with notes.

- `docs/ESDE_SD_Sync_Quick_Reference.md`  
  The **8–10** most common “real world” commands.

---

## First-Time Workflow (Recommended) ✅

1) **Audit**
   
   ```powershell
   # Summary: audit first to identify missing master cache items
   py .\sync_esde_sd.py --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" --sd_root "F:" --profile "no_videos" --audit_missing_master
   ```

2) Fix master cache gaps (re-scrape missing titles, or add media manually)

3) **Sync**
   
   ```powershell
   # Summary: perform the real sync after master cache is ready
   py .\sync_esde_sd.py --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" --sd_root "F:" --profile "no_videos" --backup_gamelist
   ```

---

## Troubleshooting ⚠️

### “Missing media” for a ROM

- If audit says media is missing, it is missing **in the NAS master cache**.
- Fix upstream by re-scraping that title into the master cache (or add media manually).

### UNC path / permissions issues

- Verify you can open `\\10.42.42.2\media\retro_gaming\ES-DE_Master` in Explorer.
- Ensure your Windows user has read access to NAS master directories.

### Fuzzy matching

- Use only when you suspect filenames differ slightly.
- Enable with:
  
  ```powershell
  # Summary: enable fuzzy matching (use when names differ slightly)
  py .\sync_esde_sd.py --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" --sd_root "F:" --profile "no_videos" --backup_gamelist --fuzzy_media_match
  ```

---

## License 📝

MIT License — see `LICENSE`.
