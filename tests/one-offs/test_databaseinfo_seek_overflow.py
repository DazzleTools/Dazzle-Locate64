"""
test_databaseinfo_seek_overflow.py
==================================

Investigates why the GUI Import flow fails with "Unable to read settings from
file '<path>\\d_drive.dbs'" while CLI search against the same database works.

Hypothesis: CDatabaseInfo::GetInfo() in DatabaseInfo.cpp uses CFile::Seek which
takes a signed LONG offset (max ~2.1 GB). For a 2.7 GB database, the per-root
dwSeekLength can exceed LONG_MAX, wrap to negative, and cause SetFilePointer to
fail. That bubbles up as GetFromFile returning NULL, which the GUI's OnImport
reports as "Unable to read settings".

This script reproduces the C++ read flow byte-for-byte against d_drive.dbs and
prints diagnostic info, including each per-root dwSeekLength and whether it
fits in a signed 32-bit LONG.

Run:
    python tests/one-offs/test_databaseinfo_seek_overflow.py

The script does NOT modify the database; it only reads.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DB_PATH = Path(r"C:\code\Dazzle-Locate32\databases\d_drive.dbs")
COMPARE_DB_PATH = Path(r"C:\code\Dazzle-Locate32\databases\devtools.dbs")

LONG_MAX = 0x7FFFFFFF  # 2,147,483,647 -- signed 32-bit upper bound
DWORD_MAX = 0xFFFFFFFF


# -----------------------------------------------------------------------------
# Helpers that mimic CFile::Read primitives from File.cpp
# -----------------------------------------------------------------------------
def read_dword(f) -> int:
    data = f.read(4)
    if len(data) != 4:
        raise EOFError(f"unexpected EOF reading DWORD at offset {f.tell()}")
    return struct.unpack("<I", data)[0]


def read_byte(f) -> int:
    data = f.read(1)
    if len(data) != 1:
        raise EOFError(f"unexpected EOF reading BYTE at offset {f.tell()}")
    return data[0]


def read_cstring_ansi(f) -> str:
    """Mirrors CFile::Read(CStringA&) -- reads bytes until 0x00."""
    out = bytearray()
    while True:
        b = f.read(1)
        if not b or b == b"\x00":
            break
        out.append(b[0])
    return out.decode("mbcs", errors="replace")


def read_cstring_unicode(f) -> str:
    """Mirrors CFile::Read(CStringW&) -- reads UTF-16LE words until 0x0000."""
    out = []
    while True:
        b = f.read(2)
        if len(b) < 2:
            break
        word = struct.unpack("<H", b)[0]
        if word == 0:
            break
        out.append(word)
    try:
        return "".join(chr(c) for c in out)
    except ValueError:
        return f"<{len(out)} unprintable wchars>"


# -----------------------------------------------------------------------------
# Replicate CDatabaseInfo::GetInfo() flow
# -----------------------------------------------------------------------------
def analyze_database(path: Path) -> dict:
    print(f"\n=== Analyzing: {path}")
    if not path.exists():
        print(f"  [SKIP] file does not exist")
        return {}

    file_size = path.stat().st_size
    print(f"  File size: {file_size:,} bytes ({file_size / (1024**3):.2f} GB)")

    info = {"path": str(path), "size": file_size, "roots": []}

    with open(path, "rb") as f:
        # 9-byte magic + version digit
        magic = f.read(9)
        if magic[:8] != b"LOCATEDB":
            print(f"  [FAIL] not a LOCATEDB file (got {magic[:8]!r})")
            return info

        version_digit = magic[8]
        if version_digit < ord("0"):
            print(f"  [FAIL] old format version byte {version_digit:#x}, this script only mimics v20+")
            return info

        bVersion = (version_digit - ord("0")) * 10
        flags = f.read(2)
        bVersion += flags[0] - ord("0")
        bLongFilenames = bool(flags[1] & 0x1)
        if flags[1] & 0x20:
            charset = "Unicode"
        elif flags[1] & 0x10:
            charset = "Ansi"
        else:
            charset = "OEM"

        print(f"  Version: {bVersion}  charset={charset}  longFilenames={bLongFilenames}")

        # Header size DWORD
        dwHeaderSize = read_dword(f)
        print(f"  dwHeaderSize: {dwHeaderSize:,} bytes")

        # Read 4 strings (creator, description, extra1, extra2)
        if charset == "Unicode":
            sCreator = read_cstring_unicode(f)
            sDescription = read_cstring_unicode(f)
            sExtra1 = read_cstring_unicode(f)
            sExtra2 = read_cstring_unicode(f)
        else:
            sCreator = read_cstring_ansi(f)
            sDescription = read_cstring_ansi(f)
            sExtra1 = read_cstring_ansi(f)
            sExtra2 = read_cstring_ansi(f)

        print(f"  Creator     : {sCreator!r}")
        print(f"  Description : {sDescription!r}")
        print(f"  sExtra1 len : {len(sExtra1)}")
        print(f"  sExtra2 len : {len(sExtra2)}")

        # Creation time + total file/dir counts
        creation_time = read_dword(f)
        total_files = read_dword(f)
        total_dirs = read_dword(f)
        print(f"  Creation time DWORD: {creation_time:#010x}")
        print(f"  Total files: {total_files:,}    Total dirs: {total_dirs:,}")

        # Loop over root blocks
        dwBlockSize = read_dword(f)
        root_idx = 0
        while dwBlockSize > 0:
            block_start_offset = f.tell()
            print(f"\n  --- Root #{root_idx} ---")
            print(f"    block_start_offset = {block_start_offset:,}")
            print(f"    dwBlockSize        = {dwBlockSize:,} ({dwBlockSize / (1024**3):.2f} GB)")

            # Compute initial dwSeekLength like the C++ code does:
            #   DWORD dwSeekLength = dwBlockSize - 1 - 4 - 4 - 4
            dwSeekLength = (dwBlockSize - 1 - 4 - 4 - 4) & DWORD_MAX
            print(f"    initial dwSeekLength = {dwSeekLength:,}")

            rtType = read_byte(f)

            if charset == "Unicode":
                sPath = read_cstring_unicode(f)
                sVolumeName = read_cstring_unicode(f)
                dwVolumeSerial = read_dword(f)
                sFileSystem = read_cstring_unicode(f)

                # In C++, the lengths are subtracted in WCHARs * 2 = bytes
                dwSeekLength = (
                    dwSeekLength
                    - (
                        (len(sPath) + 1)
                        + (len(sVolumeName) + 1)
                        + (len(sFileSystem) + 1)
                    )
                    * 2
                ) & DWORD_MAX
            else:
                sPath = read_cstring_ansi(f)
                sVolumeName = read_cstring_ansi(f)
                dwVolumeSerial = read_dword(f)
                sFileSystem = read_cstring_ansi(f)

                dwSeekLength = (
                    dwSeekLength
                    - (
                        (len(sPath) + 1)
                        + (len(sVolumeName) + 1)
                        + (len(sFileSystem) + 1)
                    )
                ) & DWORD_MAX

            root_files = read_dword(f)
            root_dirs = read_dword(f)

            print(f"    rtType        = {rtType}")
            print(f"    sPath         = {sPath!r}")
            print(f"    sVolumeName   = {sVolumeName!r}")
            print(f"    dwVolumeSerial= {dwVolumeSerial:#010x}")
            print(f"    sFileSystem   = {sFileSystem!r}")
            print(f"    root files    = {root_files:,}    root dirs = {root_dirs:,}")

            print(f"    *** dwSeekLength after subtraction = {dwSeekLength:,} (0x{dwSeekLength:08X}) ***")

            # Now interpret dwSeekLength as a signed LONG (what the C++ Seek call sees):
            signed_long = dwSeekLength if dwSeekLength <= LONG_MAX else dwSeekLength - 0x100000000
            print(f"    signed-LONG view of seek arg     = {signed_long:,}")

            if dwSeekLength > LONG_MAX:
                print(
                    f"    [BUG CONFIRMED] dwSeekLength {dwSeekLength:,} exceeds LONG_MAX "
                    f"({LONG_MAX:,}); SetFilePointer with NULL high pointer will treat "
                    f"this as a negative seek of {signed_long:,} bytes."
                )
                # Compute the position the C++ code WOULD seek to:
                cpp_target = f.tell() + signed_long
                print(f"    C++ would seek to absolute offset {cpp_target:,} (likely <0 -> failure)")

                # Also compute the correct position if the seek used a 64-bit offset:
                correct_target = f.tell() + dwSeekLength
                print(f"    Correct target offset would be    {correct_target:,}")
            else:
                print(f"    dwSeekLength fits in signed LONG; this seek would succeed.")

            # We MUST seek by the unsigned value to mimic correct behavior so we
            # can keep reading subsequent blocks.
            f.seek(dwSeekLength, 1)  # 1 = SEEK_CUR

            info["roots"].append(
                {
                    "rtType": rtType,
                    "sPath": sPath,
                    "dwBlockSize": dwBlockSize,
                    "dwSeekLength": dwSeekLength,
                    "exceeds_long_max": dwSeekLength > LONG_MAX,
                }
            )

            # Read the next root's block size
            try:
                dwBlockSize = read_dword(f)
            except EOFError:
                dwBlockSize = 0

            root_idx += 1

        print(f"\n  Header read complete; {root_idx} root(s) processed.")
        info["root_count"] = root_idx
        info["any_seek_overflow"] = any(r["exceeds_long_max"] for r in info["roots"])

    return info


def main() -> int:
    print("DatabaseInfo seek-overflow diagnostic")
    print("=====================================")
    print(f"LONG_MAX = {LONG_MAX:,} (0x{LONG_MAX:08X})\n")

    big = analyze_database(DB_PATH)
    small = analyze_database(COMPARE_DB_PATH)

    print("\n=== Summary ===")
    for label, info in (("d_drive.dbs", big), ("devtools.dbs", small)):
        if not info:
            print(f"  {label}: not analyzed")
            continue
        roots = len(info.get("roots", []))
        overflow = info.get("any_seek_overflow", False)
        size_gb = info["size"] / (1024**3)
        marker = "[BUG]" if overflow else "[OK]"
        print(
            f"  {marker} {label}: {size_gb:.2f} GB, {roots} root(s), "
            f"{'has ' if overflow else 'no '}seek overflow"
        )

    return 1 if big.get("any_seek_overflow") else 0


if __name__ == "__main__":
    sys.exit(main())
