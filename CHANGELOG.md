# Changelog

All notable changes will be documented here. Format based on [Keep a Changelog](https://keepachangelog.com/), adhering to [Semantic Versioning](https://semver.org/).

## [3.2 RC4 build 11.8221] - 2026-05-07

First Dazzle-Locate64 release candidate. Numeric version `3,2,11,8221` for the
main binaries (`locate32.exe`, `Updtdb32.exe`, `lan_en.dll`); CLI `locate.exe`
follows its own track at `3,2,11,5091`. RC4 succeeds upstream Janne Huttunen's
RC3m (`3,1,10,8220`).

### Added
- VS2022 build support (v143 platform toolset, x64 native)
- `hfcroot.props` shared property sheet for include/lib paths
- vcpkg-rebuilt 3rdparty dependencies (bzip2, PCRE, libjpeg)
- Project structure with git-repokit-template and git-repokit-common
- About dialog: "Dazzle-Locate64 (c) 2026 Dustin Darcy" contributor line alongside the original copyright
- Diagnostic one-offs `tests/one-offs/test_databaseinfo_seek_overflow.py` and `test_setfilepointer_high_dword.py` documenting the >2 GB seek-overflow bug

### Changed
- Upgraded from VS2008 `.vcproj` to VS2022 `.vcxproj` format
- Replaced `afxres.h` with `winres.h` in resource files (no MFC dependency)
- Fixed `lan_en.dll` lrestool custom build (removed hardcoded paths)
- Rebuilt `locate32.vcxproj` from scratch (VS2022 converter failure workaround)
- About dialog: replaced `GetVersionEx` with `RtlGetVersion` so Windows 10/11 are detected correctly
- About dialog: replaced `GlobalMemoryStatus` with `GlobalMemoryStatusEx` so RAM > 4 GB reports accurately on x64
- About dialog: redirected the dead `www.locate32.net` homepage and contact links to `github.com/DazzleTools/Dazzle-Locate64` and the Issues page
- About dialog: split the donation link from the donate button graphic — the inline "[donations]" text now points at `buymeacoffee.com/djdarcy` (Dazzle-Locate64 maintainer); the PayPal button graphic continues to honor the upstream author
- English language resource: visible "New versions on …" link now shows the GitHub repo URL

### Fixed
- 3rdparty library LTCG incompatibility (VS2008 libs vs VS2022 compiler)
- Missing HFCROOT include/lib paths for VS2022 (no global VC++ Directories)
- (#6) `File -> Update Database` no longer hangs at the end of the Write phase when a root resides on a substituted/UNC-mapped drive; `GetVolumeInformation` is now skipped for `DRIVE_REMOTE` / `DRIVE_NO_ROOT_DIR` / `DRIVE_UNKNOWN`
- (#7) `Tools -> Settings -> Databases -> Import` no longer fails with "Unable to read settings" on databases whose embedded settings are missing or unreadable; the GUI now offers to register the file as a new search database using its recorded root paths
- `CDatabaseInfo::GetInfo` and `GetRootsFromDatabase` no longer fail on databases larger than 2 GB; per-root seeks now pass an explicit zero high-DWORD so `SetFilePointer` treats the offset as 64-bit unsigned instead of signed `LONG` (was causing `ERROR_NEGATIVE_SEEK` on the 2.66 GB `d_drive.dbs`)

### Removed
- `.github/workflows/ci.yml` and `.github/workflows/release.yml` — both inherited from the Python-targeted `git-repokit-template` and failing every push (`pip install -e ".[dev]"` against a project with no `setup.py`/`pyproject.toml`). A C++ build pipeline + GitHub Release + installer is tracked as epic #9.

## [Upstream] - 2011-07-11

Locate32 v3.1.11.7100 by Janne Huttunen -- last official release.

[Unreleased]: https://github.com/DazzleTools/Dazzle-Locate64/commits/main
