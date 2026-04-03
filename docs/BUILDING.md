# Building Dazzle-Locate32

## Prerequisites

- **Visual Studio 2022 Community** with "Desktop development with C++" workload
- **vcpkg** (standalone at `C:\vcpkg`, or the one bundled with VS2022)
- **MSBuild** on PATH (load via "x64 Native Tools Command Prompt for VS 2022")

## Step 1: Set Up HFCROOT

HFCROOT is a directory containing the HFC library headers, compiled libraries, third-party dependencies, and build tools. The source archive provides the initial structure.

```bash
# Download the source archive (contains pre-built dependency structure)
curl -L -o vendor/locate-sources-3.1.8.9210.zip \
  "https://sourceforge.net/projects/locate32/files/sourcecode/locate-sources-3.1.8.9210.zip/download"

# Extract
mkdir vendor/source-archive-3.1.8
cd vendor/source-archive-3.1.8 && unzip ../locate-sources-3.1.8.9210.zip

# Create HFCROOT
mkdir C:\HFC
xcopy /E /I vendor\source-archive-3.1.8\locate-sources\3rdparty C:\HFC\3rdparty
xcopy /E /I vendor\source-archive-3.1.8\locate-sources\include  C:\HFC\include
xcopy /E /I vendor\source-archive-3.1.8\locate-sources\lib      C:\HFC\lib
xcopy /E /I vendor\source-archive-3.1.8\locate-sources\lib64    C:\HFC\lib64
xcopy /E /I vendor\source-archive-3.1.8\locate-sources\bin      C:\HFC\bin

# Set environment variable
setx HFCROOT "C:\HFC"
```

### HFCROOT Directory Structure

```
C:\HFC\
+-- 3rdparty\
|   +-- include\        # bzip2, PCRE, MD5, jpeglib headers
|   +-- lib\            # Win32 static libraries
|   +-- lib64\          # x64 static libraries
+-- include\            # HFC library headers (*.h, *.inl)
+-- lib\                # Win32 HFC + parsers libraries
+-- lib64\              # x64 HFC + parsers libraries
+-- bin\                # lrestool.exe
```

## Step 2: Rebuild 3rdparty Libraries via vcpkg

The source archive's pre-built libraries were compiled with VS2008 and are incompatible with VS2022's Link-Time Code Generation. Rebuild them:

```bash
vcpkg install bzip2:x64-windows-static pcre:x64-windows-static libjpeg-turbo:x64-windows-static
```

Copy with the names the source code expects:

```bash
# From vcpkg installed location (adjust path if needed)
set VCPKG=C:\vcpkg\installed\x64-windows-static

copy %VCPKG%\lib\bz2.lib         C:\HFC\3rdparty\lib64\libbz2.lib
copy %VCPKG%\lib\pcre.lib        C:\HFC\3rdparty\lib64\libpcre.lib
copy %VCPKG%\lib\jpeg.lib        C:\HFC\3rdparty\lib64\libjpeg.lib
copy %VCPKG%\debug\lib\bz2d.lib  C:\HFC\3rdparty\lib64\libbz2d.lib
copy %VCPKG%\debug\lib\pcred.lib C:\HFC\3rdparty\lib64\libpcred.lib
copy %VCPKG%\debug\lib\jpeg.lib  C:\HFC\3rdparty\lib64\libjpegd.lib
```

### Library Name Mapping

| Source `#pragma comment(lib, ...)` | vcpkg Output | Copy To |
|-----------------------------------|-------------|---------|
| `libpcre.lib` | `pcre.lib` | `3rdparty/lib64/libpcre.lib` |
| `libjpeg.lib` | `jpeg.lib` | `3rdparty/lib64/libjpeg.lib` |
| `libbz2.lib` | `bz2.lib` | `3rdparty/lib64/libbz2.lib` |
| `libmd5.lib` | (from archive) | `3rdparty/lib64/libmd5.lib` |
| `parsers.lib` | (from archive) | `lib64/parsers.lib` |

## Step 3: Build HFCLib

HFCLib must be built before the main Locate solution.

```bash
set HFCROOT=C:\HFC
MSBuild vendor\locate32-trunk\HFCLib\HFCLib.sln -p:Configuration=Release -p:Platform=x64 -m -v:minimal
```

Then copy the fresh headers and libraries to HFCROOT:

```bash
copy vendor\locate32-trunk\HFCLib\Src\*.h   C:\HFC\include\
copy vendor\locate32-trunk\HFCLib\Src\*.inl  C:\HFC\include\
copy vendor\locate32-trunk\HFCLib\HFCLib32\x64\Release\HFCLib.lib C:\HFC\lib64\
copy vendor\locate32-trunk\HFCLib\HFCCon32\x64\Release\HFCCon.lib C:\HFC\lib64\
```

## Step 4: Build Locate Solution

```bash
set HFCROOT=C:\HFC
set PATH=C:\HFC\bin;%PATH%
MSBuild vendor\locate32-trunk\Locate\locate.sln -p:Configuration=Release -p:Platform=x64 -m -v:minimal
```

Output binaries appear in `vendor\locate32-trunk\Locate\x64 - Release\bin\`.

## Build Output

| Binary | Size | Type |
|--------|------|------|
| `locate32.exe` | ~2.1 MB | GUI search application |
| `locate.exe` | ~862 KB | CLI search tool |
| `Updtdb32.exe` | ~516 KB | Database builder |
| `SetTool.exe` | ~216 KB | Settings tool |
| `lan_en.dll` | ~182 KB | English language resources |
| `keyhelper.dll` | ~104 KB | Keyboard hook helper |
| `ImgHnd.dll` | ~104 KB | Image dimension handler |
| `loc_fndx.dll` | ~125 KB | Shell find extension |

## Build Options

| Configuration | Description |
|--------------|-------------|
| `Release\|x64` | Optimized x64 build (recommended) |
| `Debug\|x64` | Debug x64 build with symbols |
| `Release(log)\|x64` | Release with debug logging |
| `Release\|Win32` | 32-bit build (not recommended for large filesystems) |

## Troubleshooting

### "Cannot open include file: 'HFCLib.h'"
HFCROOT is not set or the `hfcroot.props` file isn't being imported. Verify `HFCROOT` env var points to `C:\HFC` and that the vcxproj files import `hfcroot.props`.

### "fatal error C1047: libjpeg.lib was created by a different version"
The 3rdparty libraries need to be rebuilt with vcpkg. See Step 2.

### "Custom build for 'english.lrf' exited with code 3"
`lrestool.exe` is not on PATH. Add `C:\HFC\bin` to your PATH, or copy `lrestool.exe` to the lan_en project directory.

### "error LNK2005: CAppData::stdfunc already defined"
The `hfcroot.props` includes `/FORCE:MULTIPLE` to handle the HFCLib/HFCCon dual-link issue. If you're building a project without the props file, add `/FORCE:MULTIPLE` to the linker options.

### "cannot open include file 'afxres.h'"
Three `.rc` files reference the MFC header. Replace `#include "afxres.h"` with `#include "winres.h"` in: `FindExtension/shelldll.rc`, `ImageHandler/ImageHandler.rc`, `keyhook/keyhook.rc`.
