# ES-DE SD Sync — Quick Reference (8–10 Common Commands)

This one-page guide covers the most common, “real world” commands for `sync_esde_sd.py`.

**Constants used in examples**
- Script: `C:\Tools\ESDE-SD-Sync\sync_esde_sd.py`
- NAS master root: `\\10.42.42.2\media\retro_gaming\ES-DE_Master`
- SD root: `F:`

---

## 1) Recommended default sync ✅
**What it does**
- Filters gamelists for ROMs on SD
- Copies media per profile
- Writes SD gamelists (with backup)

```powershell
# Summary: default sync using profile "no_videos"
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # recommended profile
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 2) “Everything” sync (includes videos) 🎬
**What it does**
- Same as default sync but includes video assets

```powershell
# Summary: full sync including videos
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "everything" `                                            # includes videos
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 3) Minimal “good looking” media set 🪶
**What it does**
- Copies only a curated set of categories (small footprint)

```powershell
# Summary: sync only a minimal set of media categories
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --media "covers,marquees,screenshots,titlescreens" `                # explicit minimal set
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 4) Dry run (no changes) 🧪
**What it does**
- Shows what would be copied/written, without making changes

```powershell
# Summary: dry run preview (no writes/copies)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile to preview
  --dry_run `                                                         # preview only
  --backup_gamelist                                                   # no effect in dry run (no write)
```

---

## 5) Limit to specific systems 🎯
**What it does**
- Syncs only listed systems for faster runs

```powershell
# Summary: sync only a subset of systems
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile
  --systems "switch,ps2,snes" `                                       # only these systems
  --backup_gamelist                                                   # backup before writing
```

---

## 6) Per-ROM report (sync validation) 📋
**What it does**
- Syncs normally, and prints matched/missed categories per ROM

```powershell
# Summary: validate improved missing counts + see per-ROM report
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media profile
  --backup_gamelist `                                                 # backup gamelist before writing
  --report                                                            # per-ROM report
```

---

## 7) Fuzzy matching (only when needed) 🧩
**What it does**
- Helps when master media exists but filenames don’t match ROM stems

```powershell
# Summary: sync with fuzzy matching enabled
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile
  --backup_gamelist `                                                 # backup before writing
  --fuzzy_media_match                                                 # enable fuzzy matching
```

---

## 8) Audit missing master cache (recommended first-pass) 🔍
**What it does**
- No copies, no writes
- Reports missing metadata/media in the NAS master cache

```powershell
# Summary: audit SD ROMs vs master cache (no copies, no writes)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection
  --audit_missing_master                                              # audit-only mode
```

---

## 9) Audit + CSV checklist 🧾
**What it does**
- Builds a “to-fix” list you can work through over time

```powershell
# Summary: audit and export results to CSV checklist
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection
  --audit_missing_master `                                            # audit-only mode
  --audit_csv "C:\Temp\esde_missing_media.csv"                        # CSV output
```

---

## 10) Audit naming mismatches (maximum signal) 🧠
**What it does**
- Broadest detection for naming issues (no writes/copies)
- Suggests closest stems

```powershell
# Summary: detect likely naming mismatches and show closest suggestions
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection
  --audit_missing_master `                                            # audit-only mode
  --fuzzy_media_match `                                               # fuzzy matching
  --audit_suggest                                                     # closest-stem suggestions
