# Platform Support

## Supported Platforms

### Windows 10 / Windows 11 (Primary)

Dazzle-Locate64 is built and tested on Windows 10 and Windows 11. This is the primary target platform.

- **Architecture**: x64 (64-bit) only
- **Toolchain**: Visual Studio 2022 (v143 platform toolset)
- **Runtime**: Static CRT linking (no Visual C++ redistributable required)
- **Minimum OS**: Windows 10 version 1903 (May 2019 Update)

### Windows 7 / 8.1 (Untested)

The upstream Locate32 supported Windows XP through Windows 7. The VS2022 build targets Windows 10+ APIs by default. Compatibility with older Windows versions is not tested or guaranteed.

### Linux / macOS (Not Supported)

Locate32 is a Win32 application using the Windows API extensively (FindFirstFile, registry, shell extensions, CHM help). There are no plans for cross-platform support. For Unix-like systems, the standard `mlocate`/`plocate` packages provide equivalent functionality.

## Architecture

| Architecture | Status | Notes |
|-------------|--------|-------|
| x64 (AMD64) | Supported | Primary build target |
| Win32 (x86) | Builds but not recommended | 32-bit address space limits cause crashes on large filesystems |
| ARM64 | Not tested | VS2022 can cross-compile; untested |

## Build Configurations

| Configuration | Purpose |
|--------------|---------|
| Release x64 | Production use -- optimized, static CRT |
| Debug x64 | Development -- full debug symbols, runtime checks |
| Release(log) x64 | Release with debug logging enabled |

## Dependencies

All dependencies are statically linked. No runtime DLLs are required beyond what ships with Windows.

| Dependency | Version | Purpose |
|-----------|---------|---------|
| bzip2 | via vcpkg | Database compression |
| PCRE | via vcpkg | Regular expression search |
| libjpeg-turbo | via vcpkg | Image dimension extraction |
| MD5 | vendored | File hash computation |
| HFCLib | in-tree | Foundation C++ library (by Janne Huttunen) |

## Future Platform Considerations

- **Long path support**: Windows 10 1607+ supports paths >260 characters via manifest `longPathAware`. This needs to be enabled in the application manifest.
- **OneDrive / cloud files**: Windows 10+ introduces cloud file placeholders (reparse points) that older code may not handle gracefully.
- **NTFS USN journal**: Could enable near-instant incremental database updates instead of full directory walks.
- **Windows ARM64**: Would require testing the x64 build under emulation or setting up an ARM64 cross-compile.
