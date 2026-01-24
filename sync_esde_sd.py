r"""
Summary:
- Normal mode:
  - Scan SD:\ROMs\<system>\ for ROM files (base filename match)
  - Filter NAS master gamelist.xml to only ROMs on SD
  - Copy selected media categories from NAS master to SD:\ES-DE\
  - Write SD:\ES-DE\gamelists\<system>\gamelist.xml (optionally with backup)

- Audit mode (NEW):
  --audit_missing_master
  - Scan SD:\ROMs\<system>\ and compare against NAS master:
      <nas>\gamelists\<system>\gamelist.xml
      <nas>\downloaded_media\<system>\<category>\*
  - Report:
      - ROMs missing from master gamelist.xml (metadata missing)
      - ROMs present in master gamelist.xml but missing media for selected categories
  - Does NOT copy files and does NOT write gamelists
  - Optional CSV export via --audit_csv

Assumptions (per your structure):
- NAS master root contains:
    downloaded_media\<system>\{covers, videos, ...}
    gamelists\<system>\gamelist.xml
- SD root contains:
    ROMs\<system>\*.*
    ES-DE\downloaded_media\<system>\...
    ES-DE\gamelists\<system>\gamelist.xml
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
import xml.etree.ElementTree as ET


MEDIA_CATEGORIES_ALL = [
    "3dboxes", "backcovers", "covers", "custom", "fanart", "manuals", "marquees",
    "miximages", "physicalmedia", "screenshots", "titlescreens", "videos"
]


@dataclass
class RunStats:
    systems_seen: int = 0
    systems_processed: int = 0
    games_kept: int = 0
    games_total_in_master: int = 0
    media_files_copied: int = 0
    media_files_skipped: int = 0

    # "missing" now means: expected category had no matched media
    media_categories_attempted: int = 0
    media_categories_missing: int = 0
    categories_ignored_empty_or_missing: int = 0

    gamelists_written: int = 0


@dataclass
class AuditItem:
    system: str
    rom_filename: str
    in_master_gamelist: bool
    missing_categories: list[str]
    note: str = ""


def load_json(path: Path) -> dict:
    # Load JSON file from disk
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_rom_filename_from_xml(path_text: str) -> str:
    # Convert gamelist <path> like "./Celeste.xci" to "Celeste.xci" (lowercase)
    p = path_text.strip().replace("\\", "/")  # normalize slashes
    if p.startswith("./"):
        p = p[2:]  # strip leading "./"
    return Path(p).name.lower()  # keep only filename, case-insensitive


def normalize_stem_loose(stem: str) -> str:
    """
    Normalize a stem for fuzzy matching:
    - lower
    - remove punctuation
    - collapse whitespace
    """
    s = stem.lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)   # replace punctuation with spaces
    s = re.sub(r"\s+", " ", s).strip()   # collapse spaces
    return s


def iter_rom_files(rom_dir: Path) -> set[str]:
    # Gather all ROM filenames in a system directory (recursive), case-insensitive
    if not rom_dir.exists():
        return set()
    return {p.name.lower() for p in rom_dir.rglob("*") if p.is_file()}


def ensure_dir(path: Path, dry_run: bool) -> None:
    # Create a directory if needed
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def backup_file(path: Path, dry_run: bool) -> None:
    # Backup an existing file by copying it to <name>.bak-YYYYmmdd-HHMMSS
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-{stamp}")
    if dry_run:
        print(f"[DRY] backup: {path} -> {backup_path}")
        return
    shutil.copy2(path, backup_path)


def build_media_index(category_dir: Path, fuzzy: bool) -> tuple[dict[str, list[Path]], dict[str, list[Path]], int]:
    """
    Build indexes for fast lookup:
      exact_idx: key = lowercased stem, value = list of files with that stem
      norm_idx : key = normalized stem (punctuation removed), value = list of files
    Also returns total file count in this category directory.
    """
    exact_idx: dict[str, list[Path]] = {}
    norm_idx: dict[str, list[Path]] = {}
    total_files = 0

    if not category_dir.exists():
        return exact_idx, norm_idx, 0

    for f in category_dir.iterdir():
        if not f.is_file():
            continue
        total_files += 1
        key = f.stem.lower()
        exact_idx.setdefault(key, []).append(f)

        if fuzzy:
            nkey = normalize_stem_loose(f.stem)
            norm_idx.setdefault(nkey, []).append(f)

    return exact_idx, norm_idx, total_files


def copy_file(src: Path, dst: Path, dry_run: bool) -> str:
    """
    Copy file with skip-if-same-size logic.
    Returns: "copied" | "skipped"
    """
    ensure_dir(dst.parent, dry_run)

    if dst.exists() and src.exists():
        try:
            if dst.stat().st_size == src.stat().st_size:
                return "skipped"
        except OSError:
            pass

    if dry_run:
        print(f"[DRY] copy: {src} -> {dst}")
        return "copied"

    shutil.copy2(src, dst)
    return "copied"


def parse_category_from_media_ref(text: str, system: str) -> str | None:
    """
    Try to infer category from a media reference path inside gamelist.xml.
    Example refs often look like:
      ./downloaded_media/switch/covers/Celeste.png
    """
    if not text:
        return None

    t = text.strip().replace("\\", "/")
    parts = [p for p in t.split("/") if p and p != "."]

    # Case 1: .../downloaded_media/<system>/<category>/...
    if "downloaded_media" in parts:
        i = parts.index("downloaded_media")
        if i + 2 < len(parts) and parts[i + 1].lower() == system.lower():
            cat = parts[i + 2].lower()
            return cat if cat in MEDIA_CATEGORIES_ALL else None

    # Case 2: .../<system>/<category>/...
    lowered = [p.lower() for p in parts]
    if system.lower() in lowered:
        i = lowered.index(system.lower())
        if i + 1 < len(lowered):
            cat = lowered[i + 1]
            return cat if cat in MEDIA_CATEGORIES_ALL else None

    # Case 3: contains a known category segment somewhere
    for p in lowered:
        if p in MEDIA_CATEGORIES_ALL:
            return p

    return None


def expected_categories_from_game_xml(game: ET.Element, system: str, selected_categories: list[str]) -> set[str]:
    """
    If the <game> entry contains media references, infer which categories are expected for THIS ROM.
    If none can be inferred, returns empty set.
    """
    expected: set[str] = set()

    for child in list(game):
        if child is None or child.text is None:
            continue
        txt = child.text.strip()
        if not txt:
            continue

        if ("downloaded_media" not in txt.replace("\\", "/")) and not any(c in txt.lower() for c in MEDIA_CATEGORIES_ALL):
            continue

        cat = parse_category_from_media_ref(txt, system)
        if cat and cat in selected_categories:
            expected.add(cat)

    return expected


def suggest_closest_stem(target_stem: str, available_stems: list[str]) -> str | None:
    """
    Suggest a closest stem when mismatch likely.
    """
    if not available_stems:
        return None
    matches = get_close_matches(target_stem, available_stems, n=1, cutoff=0.80)
    return matches[0] if matches else None


def list_sd_systems(sd_root: Path) -> list[str]:
    # Discover systems by listing folders under SD:\ROMs\
    roms_root = sd_root / "ROMs"
    if not roms_root.exists():
        return []
    return sorted([p.name for p in roms_root.iterdir() if p.is_dir()])


def validate_sd_root(sd_root: Path) -> None:
    # Confirm SD root has required structure
    if not (sd_root / "ROMs").exists():
        raise SystemExit(f"SD root missing ROMs folder: {sd_root}")
    if not (sd_root / "ES-DE").exists():
        raise SystemExit(f"SD root missing ES-DE folder: {sd_root}")


def resolve_media_categories(args) -> list[str]:
    # Resolve media categories from --media or --profile + profiles.json
    profiles_path = Path(args.profiles_json)
    profiles = load_json(profiles_path) if profiles_path.exists() else {}

    if args.media.strip():
        media_categories = [m.strip() for m in args.media.split(",") if m.strip()]
    else:
        prof_name = args.profile.strip() or ("no_videos" if "no_videos" in profiles else "")
        if prof_name and prof_name in profiles:
            media_categories = list(profiles[prof_name])
        else:
            media_categories = [m for m in MEDIA_CATEGORIES_ALL if m != "videos"]

    invalid = [m for m in media_categories if m not in MEDIA_CATEGORIES_ALL]
    if invalid:
        raise SystemExit(f"Invalid media categories: {invalid}. Valid: {MEDIA_CATEGORIES_ALL}")

    return media_categories


def resolve_systems(args, sd_root: Path) -> list[str]:
    # Resolve systems from --systems or auto-detect under SD:\ROMs\
    if args.systems.strip():
        systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    else:
        systems = list_sd_systems(sd_root)

    return systems


def audit_missing_master(
    nas_master_root: Path,
    sd_root: Path,
    systems: list[str],
    media_categories_selected: list[str],
    fuzzy_media_match: bool,
    audit_suggest: bool,
    audit_csv: str | None
) -> int:
    """
    Audit-only mode:
    - No copies
    - No gamelist writes
    - Reports:
      - ROMs missing from master gamelist.xml
      - ROMs missing media for selected categories (pruned to non-empty categories)
    """
    all_items: list[AuditItem] = []

    for system in systems:
        sd_rom_dir = sd_root / "ROMs" / system
        sd_rom_files = sorted(iter_rom_files(sd_rom_dir))
        if not sd_rom_files:
            continue

        nas_gamelist = nas_master_root / "gamelists" / system / "gamelist.xml"
        nas_media_root = nas_master_root / "downloaded_media" / system

        print(f"\n=== AUDIT: {system} ===")
        print(f"SD ROMs found              : {len(sd_rom_files)}")

        if not nas_gamelist.exists():
            print(f"[WARN] Missing master gamelist.xml: {nas_gamelist}")
            # Every ROM is missing metadata in this case
            for rom in sd_rom_files:
                all_items.append(AuditItem(system, rom, False, [], "missing master gamelist.xml"))
            print(f"Missing from master gamelist: {len(sd_rom_files)}")
            continue

        # Parse master gamelist and map ROM filename -> <game> element
        tree = ET.parse(nas_gamelist)
        root = tree.getroot()
        master_games = root.findall("game")
        master_map: dict[str, ET.Element] = {}
        for game in master_games:
            p = game.find("path")
            if p is None or not p.text:
                continue
            master_map[normalize_rom_filename_from_xml(p.text)] = game

        present_in_master = 0
        missing_in_master = 0

        # Build media indexes and prune categories that are empty/missing on NAS
        effective_categories: list[str] = []
        cat_exact_idx: dict[str, dict[str, list[Path]]] = {}
        cat_norm_idx: dict[str, dict[str, list[Path]]] = {}
        ignored = 0

        for cat in media_categories_selected:
            exact_idx, norm_idx, total = build_media_index(nas_media_root / cat, fuzzy=fuzzy_media_match)
            cat_exact_idx[cat] = exact_idx
            cat_norm_idx[cat] = norm_idx

            if total > 0:
                effective_categories.append(cat)
            else:
                ignored += 1

        print(f"Selected categories         : {', '.join(media_categories_selected)}")
        print(f"Effective categories        : {', '.join(effective_categories) if effective_categories else '(none)'}")
        print(f"Categories ignored (empty)  : {ignored}")

        # Audit per ROM on SD
        missing_media_count = 0
        for rom in sd_rom_files:
            game = master_map.get(rom)
            if game is None:
                missing_in_master += 1
                all_items.append(AuditItem(system, rom, False, [], "ROM not found in master gamelist.xml"))
                continue

            present_in_master += 1

            # Determine expected categories for this ROM
            expected_from_xml = expected_categories_from_game_xml(game, system, effective_categories)
            expected_categories = sorted(expected_from_xml) if expected_from_xml else list(effective_categories)

            rom_stem = Path(rom).stem.lower()
            rom_stem_norm = normalize_stem_loose(rom_stem)

            missing_cats: list[str] = []
            for cat in expected_categories:
                matches: list[Path] = []

                # Exact stem
                matches.extend(cat_exact_idx.get(cat, {}).get(rom_stem, []))

                # Fuzzy fallbacks
                if not matches and fuzzy_media_match:
                    matches.extend(cat_norm_idx.get(cat, {}).get(rom_stem_norm, []))
                    if not matches:
                        for k, files in cat_exact_idx.get(cat, {}).items():
                            if k.startswith(rom_stem):
                                matches.extend(files)

                if not matches:
                    missing_cats.append(cat)

            if missing_cats:
                missing_media_count += 1
                note = "missing media categories in master cache"
                all_items.append(AuditItem(system, rom, True, missing_cats, note))

                # Optional suggestions (helpful when media exists but name differs)
                if audit_suggest:
                    print(f"[MISS] {rom} -> {', '.join(missing_cats)}")
                    for cat in missing_cats:
                        suggestion = suggest_closest_stem(rom_stem, list(cat_exact_idx.get(cat, {}).keys()))
                        if suggestion:
                            print(f"  💡 closest in {cat}: '{suggestion}'")

        print(f"Present in master gamelist  : {present_in_master}")
        print(f"Missing from master gamelist: {missing_in_master}")
        print(f"ROMs missing any media      : {missing_media_count}")

        # Print concise missing list (no suggestions) to avoid spam
        for item in [i for i in all_items if i.system == system and (not i.in_master_gamelist or i.missing_categories)]:
            if not item.in_master_gamelist:
                print(f"[MISSING META] {item.rom_filename}")
            elif item.missing_categories:
                print(f"[MISSING MEDIA] {item.rom_filename} -> {', '.join(item.missing_categories)}")

    # Optional CSV output
    if audit_csv:
        out = Path(audit_csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["system", "rom_filename", "in_master_gamelist", "missing_categories", "note"])
            for item in all_items:
                # Only write rows that actually represent a problem
                if (not item.in_master_gamelist) or item.missing_categories:
                    w.writerow([
                        item.system,
                        item.rom_filename,
                        "yes" if item.in_master_gamelist else "no",
                        ",".join(item.missing_categories),
                        item.note
                    ])
        print(f"\n[OK] Wrote audit CSV: {out}")

    # Return non-zero if problems exist (useful for automation)
    problems = sum(1 for i in all_items if (not i.in_master_gamelist) or i.missing_categories)
    print(f"\n=== AUDIT SUMMARY ===")
    print(f"Systems audited   : {len(systems)}")
    print(f"Issues found      : {problems}")
    print("=====================")

    return 1 if problems > 0 else 0


def filter_gamelist_and_sync_media(
    system: str,
    nas_master_root: Path,
    sd_root: Path,
    media_categories: list[str],
    dry_run: bool,
    backup_gamelist_flag: bool,
    fuzzy_media_match: bool,
    report: bool,
    stats: RunStats
) -> None:
    # Resolve key paths for this system
    sd_rom_dir = sd_root / "ROMs" / system
    sd_esde_root = sd_root / "ES-DE"
    sd_out_gamelist = sd_esde_root / "gamelists" / system / "gamelist.xml"
    sd_out_media_root = sd_esde_root / "downloaded_media" / system

    nas_gamelist = nas_master_root / "gamelists" / system / "gamelist.xml"
    nas_media_root = nas_master_root / "downloaded_media" / system

    if not nas_gamelist.exists():
        print(f"[WARN] Missing master gamelist for system '{system}': {nas_gamelist}")
        return

    rom_filenames = iter_rom_files(sd_rom_dir)
    if not rom_filenames:
        print(f"[INFO] No ROMs found for system '{system}' at: {sd_rom_dir}")
        return

    # Parse master gamelist.xml
    tree = ET.parse(nas_gamelist)
    root = tree.getroot()

    # Preserve <provider> if present
    provider = root.find("provider")

    # Build new <gameList> root
    new_root = ET.Element("gameList")
    if provider is not None:
        new_root.append(deepcopy(provider))

    # Build indexes per category; also prune categories that are missing/empty on NAS
    cat_exact_idx: dict[str, dict[str, list[Path]]] = {}
    cat_norm_idx: dict[str, dict[str, list[Path]]] = {}
    effective_categories: list[str] = []

    for cat in media_categories:
        exact_idx, norm_idx, total_files = build_media_index(nas_media_root / cat, fuzzy=fuzzy_media_match)
        cat_exact_idx[cat] = exact_idx
        cat_norm_idx[cat] = norm_idx

        if total_files > 0:
            effective_categories.append(cat)
        else:
            stats.categories_ignored_empty_or_missing += 1

    # Filter games and sync media
    master_games = root.findall("game")
    stats.games_total_in_master += len(master_games)

    kept = 0
    for game in master_games:
        path_el = game.find("path")
        if path_el is None or not path_el.text:
            continue

        rom_filename = normalize_rom_filename_from_xml(path_el.text)
        if rom_filename not in rom_filenames:
            continue

        kept += 1
        stats.games_kept += 1

        rom_stem = Path(rom_filename).stem.lower()
        rom_stem_norm = normalize_stem_loose(rom_stem)

        # Determine which categories are EXPECTED for this ROM
        expected_from_xml = expected_categories_from_game_xml(game, system, effective_categories)
        expected_categories = sorted(expected_from_xml) if expected_from_xml else list(effective_categories)

        matched_cats: list[str] = []
        missed_cats: list[str] = []

        # Copy media for expected categories only (drives accurate missing stats)
        for cat in expected_categories:
            stats.media_categories_attempted += 1

            matches: list[Path] = []

            # 1) Exact stem match
            matches.extend(cat_exact_idx.get(cat, {}).get(rom_stem, []))

            # 2) Fuzzy fallbacks
            if not matches and fuzzy_media_match:
                matches.extend(cat_norm_idx.get(cat, {}).get(rom_stem_norm, []))
                if not matches:
                    for k, files in cat_exact_idx.get(cat, {}).items():
                        if k.startswith(rom_stem):
                            matches.extend(files)

            if matches:
                matched_cats.append(cat)
                for src in matches:
                    dst = sd_out_media_root / cat / src.name
                    result = copy_file(src, dst, dry_run)
                    if result == "copied":
                        stats.media_files_copied += 1
                    else:
                        stats.media_files_skipped += 1
            else:
                missed_cats.append(cat)
                stats.media_categories_missing += 1

        # Append game node into new XML
        new_root.append(deepcopy(game))

        # Optional per-ROM report
        if report:
            expected_mode = "xml" if expected_from_xml else "heuristic"
            print(f"\n[REPORT] {system} | {Path(rom_filename).name} | expected={expected_mode}")
            print(f"  matched: {', '.join(matched_cats) if matched_cats else '(none)'}")
            print(f"  missed : {', '.join(missed_cats) if missed_cats else '(none)'}")

    # Write filtered gamelist to SD (skip write if 0 kept)
    if kept == 0:
        print(f"[INFO] System '{system}': 0 matching games found; skipping gamelist write.")
        return

    ensure_dir(sd_out_gamelist.parent, dry_run)

    if backup_gamelist_flag:
        backup_file(sd_out_gamelist, dry_run)

    if dry_run:
        print(f"[DRY] write gamelist: {sd_out_gamelist} (kept {kept} games)")
    else:
        out_tree = ET.ElementTree(new_root)
        out_tree.write(sd_out_gamelist, encoding="utf-8", xml_declaration=True)
        stats.gamelists_written += 1

    stats.systems_processed += 1
    print(f"[OK] System '{system}': kept {kept} games; media copied {stats.media_files_copied} (total so far)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nas_master_root", required=True, help=r"NAS ES-DE master root (e.g., \\10.42.42.2\...\ES-DE_Master)")
    ap.add_argument("--sd_root", required=True, help="SD drive root (e.g., F:)")
    ap.add_argument("--profile", default="", help="Media profile name (used only if --profiles_json provided)")
    ap.add_argument("--profiles_json", default="profiles.json", help="Path to profiles.json (default: profiles.json in current folder)")
    ap.add_argument("--media", default="", help="Comma-separated media categories to copy (overrides profile)")
    ap.add_argument("--systems", default="", help="Comma-separated systems to process (default: auto-detect from SD:\\ROMs)")
    ap.add_argument("--dry_run", action="store_true", help="Preview actions without copying/writing")
    ap.add_argument("--backup_gamelist", action="store_true", help="Backup existing SD gamelist.xml before writing")

    # Optional fuzzy matching
    ap.add_argument("--fuzzy_media_match", action="store_true", help="Enable normalized + prefix fallback media matching")

    # Report mode (normal sync)
    ap.add_argument("--report", action="store_true", help="Print per-ROM matched/missed categories")

    # NEW: Audit mode
    ap.add_argument("--audit_missing_master", action="store_true", help="Audit ROMs on SD vs master cache (no copies, no writes)")
    ap.add_argument("--audit_csv", default="", help=r"Optional CSV output path, e.g. C:\Temp\esde_audit.csv")
    ap.add_argument("--audit_suggest", action="store_true", help="Show closest-stem suggestions for missing media (audit mode)")

    args = ap.parse_args()

    nas_master_root = Path(args.nas_master_root)
    sd_root = Path(args.sd_root)

    # Normalize SD root like "F:" -> "F:\"
    if len(str(sd_root)) == 2 and str(sd_root).endswith(":"):
        sd_root = Path(str(sd_root) + os.sep)

    validate_sd_root(sd_root)

    media_categories = resolve_media_categories(args)
    systems = resolve_systems(args, sd_root)

    if not systems:
        print("[INFO] No systems found under SD:\\ROMs\\; nothing to do.")
        return 0

    # AUDIT MODE: no copies, no writes
    if args.audit_missing_master:
        audit_csv = args.audit_csv.strip() or None
        return audit_missing_master(
            nas_master_root=nas_master_root,
            sd_root=sd_root,
            systems=systems,
            media_categories_selected=media_categories,
            fuzzy_media_match=args.fuzzy_media_match,
            audit_suggest=args.audit_suggest,
            audit_csv=audit_csv
        )

    # NORMAL SYNC MODE
    stats = RunStats(systems_seen=len(systems))

    print("=== ES-DE SD Sync ===")
    print(f"NAS master root : {nas_master_root}")
    print(f"SD root         : {sd_root}")
    print(f"Systems         : {', '.join(systems)}")
    print(f"Media (selected): {', '.join(media_categories)}")
    print(f"Dry run         : {args.dry_run}")
    print(f"Backup gamelist : {args.backup_gamelist}")
    print(f"Fuzzy match     : {args.fuzzy_media_match}")
    print(f"Report mode     : {args.report}")
    print("=====================")

    for system in systems:
        filter_gamelist_and_sync_media(
            system=system,
            nas_master_root=nas_master_root,
            sd_root=sd_root,
            media_categories=media_categories,
            dry_run=args.dry_run,
            backup_gamelist_flag=args.backup_gamelist,
            fuzzy_media_match=args.fuzzy_media_match,
            report=args.report,
            stats=stats,
        )

    print("\n=== Summary ===")
    print(f"Systems found on SD               : {len(systems)}")
    print(f"Systems processed                 : {stats.systems_processed}")
    print(f"Master games inspected            : {stats.games_total_in_master}")
    print(f"Games kept (written)              : {stats.games_kept}")
    print(f"Gamelists written                 : {stats.gamelists_written} {'(dry-run)' if args.dry_run else ''}")
    print(f"Media files copied                : {stats.media_files_copied}")
    print(f"Media files skipped               : {stats.media_files_skipped}")
    print(f"Media categories attempted        : {stats.media_categories_attempted}")
    print(f"Media categories missing          : {stats.media_categories_missing}")
    print(f"Categories ignored (empty/missing): {stats.categories_ignored_empty_or_missing}")
    print("===============")

    return 0


if __name__ == "__main__":
    sys.exit(main())
