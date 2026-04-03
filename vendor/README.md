# Vendor Dependencies

This directory contains upstream source code and third-party dependency archives for building Dazzle-Locate32.

## locate32-trunk/ (included in repo)

The Locate32 source code from the SourceForge SVN repository, revision 236 (2012-08-15).

**Obtaining fresh checkout:**
```bash
svn checkout svn://svn.code.sf.net/p/locate32/code/trunk vendor/locate32-trunk
```

**Web browse:** https://sourceforge.net/p/locate32/code/HEAD/tree/trunk/

**License:** BSD (see `locate32-trunk/LICENCE`)

## Source Archive (not in repo -- download separately)

The source archive bundles pre-built third-party headers/libs used to bootstrap the HFCROOT build environment.

**File:** `locate-sources-3.1.8.9210.zip` (8 MB)

**Download:**
```bash
curl -L -o vendor/locate-sources-3.1.8.9210.zip \
  "https://sourceforge.net/projects/locate32/files/sourcecode/locate-sources-3.1.8.9210.zip/download"
```

**Extract to:** `vendor/source-archive-3.1.8/`
```bash
mkdir -p vendor/source-archive-3.1.8
cd vendor/source-archive-3.1.8 && unzip ../locate-sources-3.1.8.9210.zip
```

**Contents used:**
- `3rdparty/` -- bzip2, PCRE, MD5, libjpeg headers and pre-built Win32/x64 static libs
- `include/` -- HFC library headers (overwritten by fresh build)
- `lib/` / `lib64/` -- Pre-built HFC + parsers libraries
- `bin/lrestool.exe` -- Resource compilation tool for language files

**Note:** The pre-built 3rdparty libs in the archive are VS2008-era and incompatible with VS2022 LTCG. You must rebuild them via vcpkg (see below).

## Binary Release (not in repo -- for reference)

The last official Locate32 x64 binary release.

**File:** `locate32_x64-3.1.11.7100.zip` (1.3 MB)

**Download:**
```bash
curl -L -o vendor/locate32_x64-3.1.11.7100.zip \
  "https://locate32.cogit.net/download/locate32_x64-3.1.11.7100.zip"
```

There is also a newer bugfix build: `locate32_3.1.11.8220a_fix.zip`

## vcpkg Dependencies (not in repo -- install via vcpkg)

The 3rdparty static libraries must be rebuilt with VS2022 for LTCG compatibility.

```bash
vcpkg install bzip2:x64-windows-static pcre:x64-windows-static libjpeg-turbo:x64-windows-static
```

Then copy to HFCROOT with the expected library names. See [docs/BUILDING.md](../docs/BUILDING.md) for the full library name mapping.

## HFCROOT Setup

HFCROOT (`C:\HFC` by default) is the dependency root used by all projects. It's built from the source archive + vcpkg + a fresh HFCLib build. See [docs/BUILDING.md](../docs/BUILDING.md) for step-by-step setup.
