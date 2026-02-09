<#
Summary:
- Detect SD cards by finding drives that contain \ROMs and \ES-DE
- Prompt for SD drive selection and media profile
- Run the Python sync tool with those choices

Run:
  .\run_sync.ps1   # interactive

Notes:
- Uses "py" (Python launcher) if available; otherwise uses "python"
- Fixes argument passing by invoking executable + splatting remaining args
#>

Set-StrictMode -Version Latest  # enforce safer scripting

$here = Split-Path -Parent $MyInvocation.MyCommand.Path   # folder containing this script
$configPath = Join-Path $here "config.json"               # config file path
$profilesPath = Join-Path $here "profiles.json"           # profiles file path
$pyScript = Join-Path $here "sync_esde_sd.py"             # python script path

if (-not (Test-Path -LiteralPath $configPath)) { throw "Missing config.json at $configPath" }    # ensure config exists
if (-not (Test-Path -LiteralPath $profilesPath)) { throw "Missing profiles.json at $profilesPath" }# ensure profiles exists
if (-not (Test-Path -LiteralPath $pyScript)) { throw "Missing sync_esde_sd.py at $pyScript" }  # ensure python script exists

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json      # load config JSON
$profiles = Get-Content -LiteralPath $profilesPath -Raw | ConvertFrom-Json    # load profiles JSON

# Prefer Python launcher if available; fall back to python
$pythonExe = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }  # choose executable

# Enumerate filesystem drives (C:, D:, removable, etc.)
$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Root -match "^[A-Z]:\\$" }  # only normal drive roots

# Candidate SD drives must have both ROMs and ES-DE at the root
$candidates = @()
foreach ($d in $drives) {
    $roms = Join-Path $d.Root "ROMs"               # SD root ROMs folder
    $esde = Join-Path $d.Root "ES-DE"              # SD root ES-DE folder

    $hasRoms = Test-Path -LiteralPath $roms        # true if ROMs folder exists
    $hasEsde = Test-Path -LiteralPath $esde        # true if ES-DE folder exists

    if ($hasRoms -and $hasEsde) {
        # boolean AND of the two checks
        $candidates += $d                            # add drive as SD candidate
    }
}

$sdRoot = $null # Initialize sdRoot

if ($candidates.Count -eq 0) {
    Write-Warning "No candidate SD drives found automatically (needs \ROMs and \ES-DE in drive root)."
    Write-Host "You can choose from all connected external drives instead."

    # Get all "Removable" or "Fixed" volumes with a drive letter, excluding the system drive
    $allDrives = Get-Volume | Where-Object { ($_.DriveType -eq 'Fixed' -or $_.DriveType -eq 'Removable') -and $_.DriveLetter -and ($_.Path -ne ($env:SystemDrive + '\')) }

    if ($allDrives.Count -eq 0) {
        throw "No other external drives were found."
    }

    Write-Host "`nAvailable drives:"
    for ($i = 0; $i -lt $allDrives.Count; $i++) {
        $drive = $allDrives[$i]
        $driveLabel = if ([string]::IsNullOrWhiteSpace($drive.FileSystemLabel)) { "No Label" } else { $drive.FileSystemLabel }
        Write-Host ("[{0}] {1}:\ ({2})" -f $i, $drive.DriveLetter, $driveLabel)
    }

    # Use a different variable for the index to avoid conflict
    [int]$manualIdx = Read-Host "Select drive index to use as the target"
    if ($manualIdx -lt 0 -or $manualIdx -ge $allDrives.Count) { throw "Invalid selection." }

    # Set sdRoot directly
    $sdRoot = $allDrives[$manualIdx].DriveLetter + ":"
} else {
    Write-Host "Candidate SD drives:"  # show menu
    for ($i = 0; $i -lt $candidates.Count; $i++) {
        Write-Host ("[{0}] {1}" -f $i, $candidates[$i].Root)  # display each candidate
    }

    [int]$idx = Read-Host "Select SD drive index"            # prompt user
    if ($idx -lt 0 -or $idx -ge $candidates.Count) { throw "Invalid selection." }  # validate input
    $sdRoot = $candidates[$idx].Root.TrimEnd("\")            # e.g., "F:"
}

# Show profiles
$profileNames = @($profiles.PSObject.Properties.Name)    # list of preset names
Write-Host "`nMedia profiles:"
for ($i = 0; $i -lt $profileNames.Count; $i++) {
    Write-Host ("[{0}] {1}" -f $i, $profileNames[$i])      # display profile name
}

$defaultProfile = $config.default_profile                # configured default
Write-Host ("Default profile: {0}" -f $defaultProfile)   # show default

$profileChoice = Read-Host "Select profile index (Enter for default)"  # prompt

if ([string]::IsNullOrWhiteSpace($profileChoice)) {
    $profileName = $defaultProfile                          # use configured default
}
else {
    [int]$pidx = $profileChoice                             # parse index
    if ($pidx -lt 0 -or $pidx -ge $profileNames.Count) { throw "Invalid profile selection." }  # validate
    $profileName = $profileNames[$pidx]                     # selected profile name
}


# Default Systems from config
$defaultSystems = $null
if ($null -ne $config.default_systems) { $defaultSystems = $config.default_systems }

# Fuzzy Match Default from config
$fuzzyMatch = $false
if ($null -ne $config.fuzzy_media_match_default) { $fuzzyMatch = [bool]$config.fuzzy_media_match_default }

# Dry Run Default from config (default to true if missing for safety, unless config says false)
# Logic: If config has it, use it. If not, default to $true (safest).
$configDryRun = $true
if ($null -ne $config.dry_run_default) { $configDryRun = [bool]$config.dry_run_default }

# Ask for dry run
# Show distinct prompt based on default
if ($configDryRun) {
    $dryInput = Read-Host "Dry run? (Y/n)"  # Default Yes
    $dryRun = -not ($dryInput -match "^(n|no)$")
}
else {
    $dryInput = Read-Host "Dry run? (y/N)"  # Default No
    $dryRun = ($dryInput -match "^(y|yes)$")
}

# Backup setting from config (default true if missing)
$backup = $true
if ($null -ne $config.backup_gamelist) { $backup = [bool]$config.backup_gamelist }

# Build python command args
$nasRoot = $config.nas_master_root                        # NAS master root from config

$cmd = @(
    $pythonExe, $pyScript,                                  # python executable + script path
    "--nas_master_root", $nasRoot,                          # NAS master root
    "--sd_root", $sdRoot,                                   # SD root like "F:"
    "--profile", $profileName                               # profile name
)

if ($dryRun) { $cmd += "--dry_run" }                      # add dry-run flag
if ($backup) { $cmd += "--backup_gamelist" }              # add backup flag
if ($fuzzyMatch) { $cmd += "--fuzzy_media_match" }        # add fuzzy match flag
if (-not [string]::IsNullOrWhiteSpace($defaultSystems)) {
    $cmd += "--systems"
    $cmd += $defaultSystems
}

Write-Host "`nRunning:"                                   # echo command for visibility
Write-Host ($cmd -join " ")

# Execute: first element is the executable, remaining are args
& $cmd[0] @($cmd[1..($cmd.Count - 1)])
