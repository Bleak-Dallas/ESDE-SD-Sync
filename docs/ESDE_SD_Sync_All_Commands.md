# ES-DE SD Sync — **All Available Commands** (`sync_esde_sd.py`)

This document lists **every supported command pattern** for `sync_esde_sd.py`, with:
- ✅ A short summary
- ✅ What it does / what to expect
- ✅ A ready-to-run PowerShell command (with inline comments)

---

## Constants used in examples ✅

- Script: `C:\Tools\ESDE-SD-Sync\sync_esde_sd.py`
- NAS master root: `\\10.42.42.2\media\retro_gaming\ES-DE_Master`
- SD root: `F:`

> **Note:** Use `py` (recommended) or replace with `python` if you prefer.

---

# 1) Sync Mode (Copies media + writes filtered gamelist) ✅

## 1.1 Default sync using a profile
**What it does**
- Reads master `gamelist.xml` per system on NAS
- Filters it to only ROMs present on SD
- Copies selected media categories to `SD:\ES-DE\downloaded_media\...`
- Writes filtered `gamelist.xml` to `SD:\ES-DE\gamelists\<system>\gamelist.xml`

**What to expect**
- First run copies files; later runs mostly show **skipped** counts
- If `--backup_gamelist` is used, you’ll see `.bak-YYYYmmdd-HHMMSS` files created

```powershell
# Summary: sync using the "no_videos" profile (recommended default)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile from profiles.json
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 1.2 Sync using the “everything” profile (includes videos)
**What it does**
- Same as default sync, but includes `videos` (largest storage footprint)

**What to expect**
- More copy operations, significantly more SD storage usage

```powershell
# Summary: sync using the "everything" profile (includes videos)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "everything" `                                            # profile from profiles.json
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 1.3 Sync using the “artwork_only” profile (small footprint)
**What it does**
- Same as sync, but only copies the categories in `artwork_only`

**What to expect**
- Faster, smaller copies, good for smaller cards

```powershell
# Summary: sync using the "artwork_only" profile (small SD footprint)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "artwork_only" `                                          # profile from profiles.json
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 1.4 Sync with an explicit media list (overrides profile)
**What it does**
- Ignores `--profile` and copies only what you list in `--media`

**What to expect**
- Precise control over SD usage and copy time

```powershell
# Summary: sync only a specific set of media categories (overrides any profile)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --media "covers,marquees,screenshots,titlescreens" `                # explicit categories (overrides profile)
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 1.5 Dry run sync (no writes, no copies)
**What it does**
- Computes what would happen but makes **no changes**

**What to expect**
- Output lines prefixed with `[DRY]`
- No new files created and no copies performed

```powershell
# Summary: preview sync actions without copying or writing anything
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile from profiles.json
  --dry_run `                                                         # do not write/copy; print only
  --backup_gamelist                                                   # ignored in practice during dry run (no write)
```

---

## 1.6 Sync without backing up gamelists
**What it does**
- Writes the filtered gamelist directly (no `.bak-*`)

**What to expect**
- Faster and less clutter, but no rollback without your own backups

```powershell
# Summary: sync without backing up SD gamelist.xml (not recommended unless you have other backups)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos"                                               # profile from profiles.json
```

---

## 1.7 Sync only selected systems (limits scope)
**What it does**
- Only processes the systems you list

**What to expect**
- Faster runs; avoids touching other system folders on the SD

```powershell
# Summary: sync only the selected systems (comma-separated)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile from profiles.json
  --systems "switch,ps2,snes" `                                       # only these systems
  --backup_gamelist                                                   # backup SD gamelist.xml before writing
```

---

## 1.8 Sync with per-ROM report
**What it does**
- Performs normal sync AND prints per-ROM matched/missed categories

**What to expect**
- Verbose output; ideal for validating a new device/system naming convention

```powershell
# Summary: sync and print per-ROM matched/missed categories
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile from profiles.json
  --backup_gamelist `                                                 # backup SD gamelist.xml before writing
  --report                                                            # per-ROM report output
```

---

## 1.9 Sync with fuzzy media matching
**What it does**
- Performs normal sync but expands media matching:
  - exact stem first
  - then normalized match (punctuation/spacing)
  - then prefix fallback

**What to expect**
- Can recover media when naming differs slightly
- Small risk of false positives on extremely similar titles

```powershell
# Summary: sync with fuzzy matching enabled (use when media exists but names differ)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile from profiles.json
  --backup_gamelist `                                                 # backup SD gamelist.xml before writing
  --fuzzy_media_match                                                 # enable fuzzy matching
```

---

## 1.10 Sync with fuzzy matching + per-ROM report (best troubleshooting)
**What it does**
- Combines maximum visibility with maximum matching flexibility

**What to expect**
- Most verbose sync output
- Best single command when diagnosing a tricky title

```powershell
# Summary: sync with fuzzy matching and per-ROM reporting (best troubleshooting combo)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # profile from profiles.json
  --backup_gamelist `                                                 # backup SD gamelist.xml before writing
  --report `                                                          # per-ROM report output
  --fuzzy_media_match                                                 # enable fuzzy matching
```

---

# 2) Audit Mode (No copies + no writes) 🔍

Audit mode is activated by `--audit_missing_master`.

## 2.1 Basic audit (recommended)
**What it does**
- Scans ROMs on SD per system
- Checks whether each ROM is present in the NAS master `gamelist.xml`
- For ROMs present in the master, checks whether media exists in selected categories

**What to expect**
- Output lines:
  - `[MISSING META]` for ROMs not in master gamelist
  - `[MISSING MEDIA]` for ROMs missing assets in master cache

```powershell
# Summary: audit SD ROMs vs master cache (no copies, no writes)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection for audit
  --audit_missing_master                                              # audit-only mode (no writes/copies)
```

---

## 2.2 Audit using “everything” categories
**What it does**
- Same as audit, but checks also for `videos`

**What to expect**
- More “missing media” findings, because videos are often absent for many games

```powershell
# Summary: audit against the "everything" profile (includes videos)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "everything" `                                            # media selection for audit
  --audit_missing_master                                              # audit-only mode (no writes/copies)
```

---

## 2.3 Audit with an explicit media list (overrides profile)
**What it does**
- Audits only the categories you specify

**What to expect**
- A focused audit checklist (e.g., “only covers + screenshots”)

```powershell
# Summary: audit only selected media categories (overrides any profile)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --media "covers,marquees,screenshots,titlescreens" `                # explicit audit categories
  --audit_missing_master                                              # audit-only mode (no writes/copies)
```

---

## 2.4 Audit only selected systems
**What it does**
- Audits only the systems you specify

**What to expect**
- Faster output and smaller CSVs

```powershell
# Summary: audit only the selected systems (comma-separated)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection for audit
  --systems "switch,ps2" `                                            # only these systems
  --audit_missing_master                                              # audit-only mode (no writes/copies)
```

---

## 2.5 Audit with CSV export
**What it does**
- Runs audit and writes a CSV containing only “problem rows”:
  - missing metadata OR missing media categories

**What to expect**
- Output confirms CSV location
- CSV columns: `system, rom_filename, in_master_gamelist, missing_categories, note`

```powershell
# Summary: audit and export results to CSV (missing-only rows)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection for audit
  --audit_missing_master `                                            # audit-only mode (no writes/copies)
  --audit_csv "C:\Temp\esde_missing_media.csv"                        # write CSV checklist
```

---

## 2.6 Audit with suggestions (closest-stem hints)
**What it does**
- Runs audit and, for missing media, prints likely name mismatches:
  - “closest stem in covers: '...'”

**What to expect**
- More verbose output
- Useful when you suspect the master cache *has* files, but names differ

```powershell
# Summary: audit and show closest-stem suggestions for missing media
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection for audit
  --audit_missing_master `                                            # audit-only mode (no writes/copies)
  --audit_suggest                                                     # show closest-stem suggestions
```

---

## 2.7 Audit with fuzzy matching
**What it does**
- Expands audit matching logic to detect cases where media exists but naming differs slightly

**What to expect**
- Fewer “missing media” results when the issue is purely naming mismatch

```powershell
# Summary: audit with fuzzy matching enabled (detect naming mismatches)
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master root
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection for audit
  --audit_missing_master `                                            # audit-only mode (no writes/copies)
  --fuzzy_media_match                                                 # enable fuzzy matching
```

---

## 2.8 Audit with fuzzy matching + suggestions (strongest mismatch detector)
**What it does**
- Best audit command when you suspect the master cache contains files but names don’t match

**What to expect**
- Most verbose audit output
- Suggestions help you decide whether to rename or adjust scraping rules

```powershell
# Summary: detect likely naming mismatches and show closest suggestions
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master
  --sd_root "F:" `                                                    # SD root
  --profile "no_videos" `                                             # media selection
  --audit_missing_master `                                            # audit-only mode
  --fuzzy_media_match `                                               # fuzzy matching
  --audit_suggest                                                     # closest-stem suggestions
```

---

## 2.9 Audit only selected systems + CSV + fuzzy + suggestions (maximum audit)
**What it does**
- A full “enterprise audit” style run for targeted systems

**What to expect**
- Verbose console output plus a CSV checklist you can work from

```powershell
# Summary: maximum audit for selected systems with CSV + fuzzy + suggestions
py C:\Tools\ESDE-SD-Sync\sync_esde_sd.py `                            # run script
  --nas_master_root "\\10.42.42.2\media\retro_gaming\ES-DE_Master" `  # NAS master
  --sd_root "F:" `                                                    # SD root
  --systems "switch,ps2" `                                            # only these systems
  --profile "no_videos" `                                             # media selection
  --audit_missing_master `                                            # audit-only mode
  --audit_csv "C:\Temp\esde_audit_switch_ps2.csv" `                   # CSV output
  --fuzzy_media_match `                                               # fuzzy matching
  --audit_suggest                                                     # closest-stem suggestions
```

---

# 3) Reference: Full Argument List (for completeness) 📌

**Required**
- `--nas_master_root <path>`
- `--sd_root <drive>`

**Media Selection**
- `--profile <name>`
- `--profiles_json <path>`
- `--media <comma-separated categories>`

**Scope**
- `--systems <comma-separated systems>`

**Sync Controls**
- `--dry_run`
- `--backup_gamelist`
- `--report`
- `--fuzzy_media_match`

**Audit Controls**
- `--audit_missing_master`
- `--audit_csv <path>`
- `--audit_suggest`
