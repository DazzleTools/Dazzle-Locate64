# Contributing to Dazzle-Locate64

Thank you for considering contributing to Dazzle-Locate64!

## Development Setup

### Prerequisites

- **Visual Studio 2022 Community** (with "Desktop development with C++" workload)
- **vcpkg** (bundled with VS2022 at `C:\vcpkg`, or standalone)
- **Git**

### Clone and Build

```bash
git clone https://github.com/DazzleTools/Dazzle-Locate64.git
cd Dazzle-Locate64
```

See [docs/BUILDING.md](docs/BUILDING.md) for the full build guide.

### Quick Build (VS Developer Command Prompt)

```bash
# Install dependencies
vcpkg install bzip2:x64-windows-static pcre:x64-windows-static libjpeg-turbo:x64-windows-static

# Set HFCROOT
set HFCROOT=C:\HFC

# Build HFCLib first
MSBuild vendor\locate32-trunk\HFCLib\HFCLib.sln -p:Configuration=Release -p:Platform=x64

# Build Locate
MSBuild vendor\locate32-trunk\Locate\locate.sln -p:Configuration=Release -p:Platform=x64
```

### Testing

```bash
# Create a test database from a small directory
Updtdb32.exe -d test.dbs -cU -L "C:\code\Dazzle-Locate64"

# Verify search works
locate.exe -d test.dbs "updatedb.cpp"
```

## Project Structure

```
vendor/
  locate32-trunk/          # Upstream SVN source (r236)
    HFCLib/                # Foundation C++ library (build first)
    Locate/                # Main application solution (11 projects)
      hfcroot.props        # Shared include/lib path configuration
      Locate32/            # GUI application
      locate/              # CLI search tool
      updatedb/            # Database builder
      LocateDB/            # Database format library
      Locater/             # Search engine library
      common/              # Shared utilities
scripts/                   # git-repokit-common subtree (hooks, tools)
docs/                      # Build guides, documentation
tests/
  one-offs/                # Quick checks, proof-of-concept scripts
```

## Key Design Principles

1. **Upstream compatibility** -- preserve the original Locate32 database format and CLI interface
2. **x64 first** -- all new work targets x64; fix 32-bit assumptions as we find them
3. **One-offs graduate** -- quick tests in `tests/one-offs/` can be promoted to proper tests
4. **Clean commits** -- descriptive commit messages explaining the "why"

## Code Style

- C++ with Win32 API (no .NET, no managed code)
- Follow existing HFCLib conventions for new code in vendor/
- New standalone tools can use modern C++17

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test with a fresh build and database creation
5. Submit a pull request with a clear description
