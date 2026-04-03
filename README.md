# Dazzle-Locate64

[![C++](https://img.shields.io/badge/C++-Win32-blue.svg)](https://en.cppreference.com/w/cpp)
[![Visual Studio 2022](https://img.shields.io/badge/VS2022-v143-blue.svg)](https://visualstudio.microsoft.com/vs/)
[![vcpkg](https://img.shields.io/badge/vcpkg-package%20manager-blue.svg)](https://vcpkg.io/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub release](https://img.shields.io/github/v/release/DazzleTools/Dazzle-Locate64?include_prereleases)](https://github.com/DazzleTools/Dazzle-Locate64/releases)
[![GitHub Discussions](https://img.shields.io/github/discussions/DazzleTools/Dazzle-Locate64)](https://github.com/DazzleTools/Dazzle-Locate64/discussions)

[![Windows](https://img.shields.io/badge/Windows-10%2F11-brightgreen.svg)](docs/PLATFORMS.md)

**A modernized fork of [Locate32](https://locate32.cogit.net/) for Windows 10/11 -- fast file indexing and search for large filesystems with hundreds of millions of files.**

> **Upstream**: Locate32 v3.1.11 by Janne Huttunen (BSD license, last updated 2011). This fork builds with VS2022 as native x64.

## The Problem

Windows search is slow on large developer machines. When you have hundreds of millions of files across multiple drives, finding a specific file by name can take 30+ seconds with Explorer search. Tools like [Everything](https://www.voidtools.com/) exist, but Locate32 offers a Unix `locate`/`updatedb` model: a pre-built database that enables instant filename searches, including CLI integration with editors like Vim.

The original Locate32 hasn't been updated since 2011. The last available binary is **32-bit**, which crashes when indexing very large filesystems due to address space and integer overflow limitations.

## The Solution

Dazzle-Locate64 modernizes the Locate32 codebase:

- **x64 native build** -- no more 32-bit address space crashes
- **VS2022 toolchain** -- modern compiler with security mitigations (ASLR, CFG)
- **vcpkg dependencies** -- reproducible builds of bzip2, PCRE, libjpeg
- **Windows 10/11 compatibility** -- long path support, modern filesystem handling (planned)

## Features

- **Instant file search**: Query millions of filenames in under a second
- **Multiple databases**: One per drive, or custom project-specific databases
- **CLI + GUI**: `locate.exe` for scripts/editors, `locate32.exe` for interactive use
- **Vim integration**: Pair with `LOCATEIT()` for instant file-open from Vim
- **Scheduled updates**: Run `Updtdb32.exe` nightly via Task Scheduler
- **Unicode support**: Full Unicode filename indexing
- **Shell extension**: Right-click "Find with Locate32" in Explorer

## Installation

### Download Pre-built Binaries (Recommended)

Download the latest release from the [Releases page](https://github.com/DazzleTools/Dazzle-Locate64/releases):

| Binary | Purpose |
|--------|---------|
| `locate32.exe` | GUI search application |
| `locate.exe` | CLI search tool |
| `Updtdb32.exe` | Database builder/updater |
| `SetTool.exe` | Settings configuration |
| `lan_en.dll` | English language resources |
| `keyhelper.dll` | Keyboard hook helper |
| `ImgHnd.dll` | Image dimension handler |
| `loc_fndx.dll` | Shell find extension |

Place all files in a single directory and add it to your PATH.

### Build from Source

**Prerequisites:**
- Visual Studio 2022 Community (with C++ workload)
- vcpkg (bundled with VS2022, or standalone at `C:\vcpkg`)

**Quick build:**
```bash
# Install 3rdparty dependencies
vcpkg install bzip2:x64-windows-static pcre:x64-windows-static libjpeg-turbo:x64-windows-static

# Build (from VS Developer Command Prompt)
MSBuild vendor\locate32-trunk\HFCLib\HFCLib.sln -p:Configuration=Release -p:Platform=x64
MSBuild vendor\locate32-trunk\Locate\locate.sln -p:Configuration=Release -p:Platform=x64
```

For detailed build instructions, see the [Building Guide](docs/BUILDING.md).

## Usage

### Build a Database

```bash
# Index specific directories
Updtdb32.exe -d devtools.dbs -cU -L "C:\code" -L "Z:\wintools"

# Index an entire drive
Updtdb32.exe -d c_drive.dbs -cU -L "C:\"

# Quiet mode (for scheduled tasks)
Updtdb32.exe -d c_drive.dbs -cU -L "C:\" -q
```

### Search

```bash
# Search for files
locate.exe -d devtools.dbs "updatedb.cpp"

# Search with a specific database
locate.exe -d "C:\Locate32\databases\c_drive.dbs" "*.py"
```

### Vim Integration

Add to your `_vimrc`:
```vim
function! LOCATEIT(param)
    let l:inp = input("")
    if strlen(l:inp) == 0
        return
    endif
    let l:cmd = strlen(a:param) > 0 ? "locate " . a:param . " " . l:inp : "locate " . l:inp
    let l:output = system(l:cmd)
    let l:lines = split(l:output, '\n')
    let l:sel = inputlist(map(copy(l:lines), 'v:key+1 . ": " . v:val'))
    if l:sel > 0 && l:sel <= len(l:lines)
        execute "tabnew " . l:lines[l:sel-1]
    endif
endfunction

map <leader>op :call LOCATEIT('-d "C:\path\to\your\database.dbs"')<enter>
```

### Updtdb32.exe Options

| Option | Description |
|--------|-------------|
| `-d file` | Output database file |
| `-L path` | Directory to index (repeatable) |
| `-L1` | Index all local hard drives |
| `-E path` | Exclude directory |
| `-e pattern` | Exclude files matching pattern |
| `-cU` | Use Unicode character set |
| `-cA` | Use ANSI character set |
| `-I` | Incremental update |
| `-q` | Quiet mode |
| `-h` | Show help |

## How It Works

1. **Database build** (`Updtdb32.exe`): Walks directory trees and stores filenames in a compressed `.dbs` database file
2. **Search** (`locate.exe` / `locate32.exe`): Scans the pre-built database for pattern matches -- no filesystem access needed
3. **Nightly updates**: Schedule `Updtdb32.exe` via Windows Task Scheduler to keep the database current

## Development

### Project Structure

```
Dazzle-Locate64/
+-- vendor/
|   +-- locate32-trunk/       # SVN r236 source (upstream)
|   |   +-- HFCLib/           # Foundation C++ library
|   |   +-- Locate/           # Main application (11 projects)
|   |   |   +-- hfcroot.props # Shared include/lib paths
|   |   |   +-- Locate32/     # GUI app
|   |   |   +-- locate/       # CLI search
|   |   |   +-- updatedb/     # Database builder
|   |   |   +-- LocateDB/     # Database library
|   |   |   +-- Locater/      # Search engine library
|   |   |   +-- common/       # Shared utilities
|   |   +-- lrestool/         # Resource compilation tool
+-- scripts/                  # git-repokit-common subtree
+-- docs/
+-- tests/
```

### Building for Development

See [docs/BUILDING.md](docs/BUILDING.md) for the full build guide, including HFCROOT setup and dependency details.

## Contributions

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

Like the project?

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/djdarcy)

## Acknowledgements

- **Janne Huttunen** -- Original Locate32 author (1997-2011)
- Part of the [DazzleTools](https://github.com/DazzleTools) collection

## License

Dazzle-Locate64, Copyright (C) 2026 Dustin Darcy ([@djdarcy](https://github.com/djdarcy))

This project is licensed under the GNU General Public License v3.0 -- see the [LICENSE](LICENSE) file for details.

The original Locate32 source (in `vendor/locate32-trunk/`) is BSD-licensed by Janne Huttunen. See [vendor/locate32-trunk/LICENCE](vendor/locate32-trunk/LICENCE) for the upstream license.
