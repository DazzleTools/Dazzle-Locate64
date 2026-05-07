<#
.SYNOPSIS
  Bundle the locally-built Dazzle-Locate64 binaries into a release zip.

.DESCRIPTION
  This is a manual release-packager intended for use until the full CI build
  pipeline (#9) is implemented. It collects the binaries produced by an
  x64 Release build of vendor/locate32-trunk/Locate/locate.sln and zips
  them up alongside README / LICENSE / CHANGELOG.

  Usage:
      pwsh scripts\package_release.ps1
      pwsh scripts\package_release.ps1 -Version "3.2-RC4-build11.8221"
      pwsh scripts\package_release.ps1 -OutputDir "C:\releases" -Version "..."

.PARAMETER Version
  Optional version string for the output filename. If omitted, parsed from
  englishrc.rc.

.PARAMETER OutputDir
  Parent destination directory. Defaults to "release-artifacts" under the
  project root. The script then writes to "<OutputDir>/v<Version>/" so each
  release lives in its own directory alongside its release-notes.md (matching
  the convention used by xormove).

.PARAMETER BinDir
  Source directory containing the built binaries. Defaults to the project's
  vendor/locate32-trunk/Locate/x64 - Release/bin path.

.NOTES
  - Verifies the project root by looking for CHANGELOG.md.
  - Always packs the eight production binaries (locate32.exe, locate.exe,
    Updtdb32.exe, lan_en.dll, ImgHnd.dll, keyhelper.dll, loc_fndx.dll,
    SetTool.exe).
  - Will fail loudly if any binary is missing.
  - Includes LICENSE, README.md, CHANGELOG.md at the zip root.
  - Skips databases/ and any other working files.
#>
[CmdletBinding()]
param(
    [string]$Version,
    [string]$OutputDir,
    [string]$BinDir
)

$ErrorActionPreference = 'Stop'

# --- Locate project root --------------------------------------------------
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot "..") | Select-Object -ExpandProperty Path
if (-not (Test-Path (Join-Path $projectRoot "CHANGELOG.md"))) {
    throw "Cannot locate project root from script path '$scriptRoot'. Expected CHANGELOG.md at parent."
}

# --- Resolve defaults -----------------------------------------------------
if (-not $BinDir) {
    $BinDir = Join-Path $projectRoot "vendor\locate32-trunk\Locate\x64 - Release\bin"
}
if (-not (Test-Path $BinDir)) {
    throw "Build output directory not found: $BinDir`nRun an x64 Release build of locate.sln first."
}

if (-not $Version) {
    $rcPath = Join-Path $projectRoot "vendor\locate32-trunk\Locate\Locate32\commonres.rc"
    $rcText = [System.Text.Encoding]::GetEncoding(1252).GetString([System.IO.File]::ReadAllBytes($rcPath))
    $m = [regex]::Match($rcText, 'VALUE "ProductVersion", "([^"]+)"')
    if (-not $m.Success) {
        throw "Could not parse ProductVersion from $rcPath"
    }
    $raw = $m.Groups[1].Value          # e.g. "3.2 RC4 build 11.8221"
    $Version = ($raw -replace ' build ', '-build') -replace ' ', '-'
    Write-Host "Detected version: $Version"
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $projectRoot "release-artifacts"
}
$versionDir = Join-Path $OutputDir "v$Version"
if (-not (Test-Path $versionDir)) {
    New-Item -ItemType Directory -Path $versionDir -Force | Out-Null
}

# --- Required binaries ----------------------------------------------------
$requiredBinaries = @(
    'locate32.exe',     # GUI
    'locate.exe',       # CLI
    'Updtdb32.exe',     # Database updater
    'lan_en.dll',       # English language pack
    'ImgHnd.dll',       # Image preview shell extension
    'keyhelper.dll',    # Hotkey hook
    'loc_fndx.dll',     # FindExtension shell extension
    'SetTool.exe'       # Settings tool
)

# --- Stage files ----------------------------------------------------------
$bundleName = "Dazzle-Locate64-$Version"
$stage = Join-Path $env:TEMP "dl64-package-$([guid]::NewGuid().ToString('N').Substring(0,8))"
$stageBundle = Join-Path $stage $bundleName
New-Item -ItemType Directory -Path $stageBundle -Force | Out-Null
Write-Host "Staging in: $stageBundle"

# Copy binaries
$missing = @()
foreach ($name in $requiredBinaries) {
    $src = Join-Path $BinDir $name
    if (-not (Test-Path $src)) {
        $missing += $name
        continue
    }
    Copy-Item $src $stageBundle -Force
}
if ($missing.Count -gt 0) {
    throw "Missing built binaries in '$BinDir':`n  - $($missing -join "`n  - ")"
}

# Copy doc files
foreach ($docFile in @('LICENSE', 'README.md', 'CHANGELOG.md')) {
    $src = Join-Path $projectRoot $docFile
    if (Test-Path $src) {
        Copy-Item $src $stageBundle -Force
    } else {
        Write-Warning "Skipping missing doc: $docFile"
    }
}

# --- Verify each binary is x64 PE32+ -------------------------------------
foreach ($name in $requiredBinaries) {
    $f = Join-Path $stageBundle $name
    $bytes = [System.IO.File]::ReadAllBytes($f)
    if ($bytes.Length -lt 512) { throw "$name suspiciously small ($($bytes.Length) bytes)" }
    if ($bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) { throw "$name not a PE binary (no MZ header)" }
    # PE header offset at 0x3C, machine type at PE+4 should be 0x8664 for x64
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3C)
    if ($peOffset -le 0 -or $peOffset -gt $bytes.Length - 6) { throw "$name invalid PE offset" }
    $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
    if ($machine -ne 0x8664) { throw "$name is not x64 (machine = 0x$($machine.ToString('X4')))" }
}
Write-Host "  [OK] All 8 binaries verified as x64 PE32+"

# --- Create zip -----------------------------------------------------------
$zipPath = Join-Path $versionDir "Dazzle-Locate64-windows-x64.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

# Use Compress-Archive (built-in)
Compress-Archive -Path $stageBundle -DestinationPath $zipPath -CompressionLevel Optimal

# --- Cleanup --------------------------------------------------------------
Remove-Item $stage -Recurse -Force

# --- Report ---------------------------------------------------------------
$zipInfo = Get-Item $zipPath
$sha = (Get-FileHash $zipPath -Algorithm SHA256).Hash
$relZip = $zipPath.Substring($projectRoot.Length).TrimStart('\','/')
Write-Host ""
Write-Host "=== Release bundle ready ==="
Write-Host "  Dir   : $versionDir"
Write-Host "  Zip   : $relZip"
Write-Host "  Size  : $([math]::Round($zipInfo.Length / 1MB, 2)) MB ($($zipInfo.Length) bytes)"
Write-Host "  SHA256: $sha"
Write-Host ""
Write-Host "Next steps (manual):"
Write-Host "  1. Drop release-notes.md into '$versionDir' (write or copy from CHANGELOG)"
Write-Host "  2. git push origin main"
Write-Host "  3. git tag -a v$Version -m 'Dazzle-Locate64 v$Version'"
Write-Host "  4. git push origin v$Version"
Write-Host "  5. gh release create v$Version `"$zipPath`" \"
Write-Host "        --notes-file `"$versionDir\release-notes.md`" --prerelease"
