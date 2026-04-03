# Changelog

All notable changes will be documented here. Format based on [Keep a Changelog](https://keepachangelog.com/), adhering to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- VS2022 build support (v143 platform toolset, x64 native)
- `hfcroot.props` shared property sheet for include/lib paths
- vcpkg-rebuilt 3rdparty dependencies (bzip2, PCRE, libjpeg)
- Project structure with git-repokit-template and git-repokit-common

### Changed
- Upgraded from VS2008 `.vcproj` to VS2022 `.vcxproj` format
- Replaced `afxres.h` with `winres.h` in resource files (no MFC dependency)
- Fixed `lan_en.dll` lrestool custom build (removed hardcoded paths)
- Rebuilt `locate32.vcxproj` from scratch (VS2022 converter failure workaround)

### Fixed
- 3rdparty library LTCG incompatibility (VS2008 libs vs VS2022 compiler)
- Missing HFCROOT include/lib paths for VS2022 (no global VC++ Directories)

## [Upstream] - 2011-07-11

Locate32 v3.1.11.7100 by Janne Huttunen -- last official release.

[Unreleased]: https://github.com/DazzleTools/Dazzle-Locate64/commits/main
