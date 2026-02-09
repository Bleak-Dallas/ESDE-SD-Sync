# GEMINI.md: Project Overview for ES-DE SD Sync

This document provides a high-level summary of the `ESDE-SD-Sync` project for use as a context for AI-assisted development.

## 1. Project Overview

**Purpose:** `ESDE-SD-Sync` is a command-line utility for synchronizing game metadata for the [EmulationStation-DE (ES-DE)](https://www.es-de.org/) front-end. Its primary goal is to solve the problem of re-scraping game metadata (like artwork, videos, and descriptions) for every new handheld device. It does this by maintaining a single **NAS master cache** of scraped data and providing a script to intelligently copy a subset of that data to a device's SD card.

**Architecture:**
*   **Master Source:** A central file share (NAS) that holds a complete collection of `gamelist.xml` files and `downloaded_media` for all game systems.
*   **Target:** An SD card containing a `ROMs` folder for a specific device.
*   **Process:** The script scans the ROMs on the SD card, filters the master `gamelist.xml` to include only those games, and copies the relevant media files based on a user-selected profile.

**Technology:**
*   **Core Logic:** A single Python script (`sync_esde_sd.py`) written with standard libraries (`argparse`, `xml`, `pathlib`). It has **no external dependencies**.
*   **Wrapper:** An interactive PowerShell wrapper (`run_sync.ps1`) provides a user-friendly way to run the script by detecting drives and prompting for input.
*   **Configuration:** The project uses JSON files (`config.json`, `profiles.json`) to manage settings and media profiles.

## 2. Building and Running

This project does not require a build or compilation step.

### Running the Interactive Wrapper (Recommended)

The easiest way to run the tool is with the PowerShell wrapper, which interactively prompts for the SD card and media profile.

```powershell
.\run_sync.ps1
```

### Running the Python Script Directly

The core script can be executed directly, which is useful for automation or when not using PowerShell. The script takes several command-line arguments to specify the source, destination, and behavior.

**Key Arguments:**
*   `--nas_master_root`: Path to the master ES-DE media and gamelist directory on the NAS.
*   `--sd_root`: The root of the target SD card (e.g., `F:`).
*   `--profile`: The name of a media profile defined in `profiles.json` (e.g., `no_videos`).
*   `--audit_missing_master`: A flag to run in "audit" mode, which reports on missing metadata and media in the master cache without writing any files to the SD card.
*   `--dry_run`: A flag to simulate the sync process without copying or writing any files.

**Example Sync Command:**
```powershell
py .\sync_esde_sd.py --nas_master_root "\\NAS\ES-DE_Master" --sd_root "F:" --profile "no_videos" --backup_gamelist
```

**Example Audit Command:**
```powershell
py .\sync_esde_sd.py --nas_master_root "\\NAS\ES-DE_Master" --sd_root "F:" --profile "no_videos" --audit_missing_master
```

## 3. Development Conventions

*   **Core Logic:** All primary functionality resides in `sync_esde_sd.py`. It is self-contained and uses modern Python features like `pathlib` and `dataclasses`.
*   **Configuration:**
    *   `profiles.json`: Defines named collections of media categories (e.g., "artwork_only", "no_videos"). This is used by the core Python script.
    *   `config.json`: Stores default paths and settings for the `run_sync.ps1` interactive wrapper. It is **not** read by the core Python script.
*   **Testing:** There are no automated tests in the repository. However, the script's `--dry_run` and `--audit_missing_master` flags are the primary means of testing and verification before making changes.
*   **Documentation:** The `docs/` directory contains detailed command references. `README.md` provides a comprehensive user guide.
*   **Dependencies:** The project is intentionally designed with zero external Python dependencies, simplifying setup and execution.

## 🛠 Custom Commands

### /plan [task]
When I use this command, follow these steps before writing code:
1. **Analyze:** Locate the relevant sections in `sync_esde_sd.py` or `run_sync.ps1`.
2. **Review Config:** Check if `profiles.json` or `config.json` need schema changes.
3. **Draft:** Provide a bulleted list of the logic changes.
4. **Safety Check:** Explicitly state how we will use `--dry_run` to verify the fix.
5. **Wait:** Do not apply changes until I say "GO."