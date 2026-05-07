"""
test_setfilepointer_high_dword.py
=================================

Validates the FIX for the LOCATEDB-info seek overflow. The fix in
DatabaseInfo.cpp passes an explicit zero high-DWORD pointer to CFile::Seek
which forwards to Win32 SetFilePointer. With the high pointer non-NULL,
SetFilePointer treats the (lDistanceToMove, *lpDistanceToMoveHigh) pair as a
single 64-bit signed value -- so a DWORD low offset whose top bit is set is
NOT interpreted as a negative LONG.

This script reproduces both behaviors against d_drive.dbs:

  Case A: SetFilePointer(handle, (LONG)dwSeekLength, NULL, FILE_CURRENT)
          -- this is the BUGGY pre-fix call. Expect failure / wrong position.

  Case B: SetFilePointer(handle, (LONG)dwSeekLength, &lZero, FILE_CURRENT)
          where lZero = 0
          -- this is the POST-FIX call. Expect success at +2.66 GB.

Run:
    python tests/one-offs/test_setfilepointer_high_dword.py

The script does NOT modify the database; it only seeks within it.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import sys
from pathlib import Path

DB_PATH = Path(r"C:\code\Dazzle-Locate32\databases\d_drive.dbs")
SEEK_OFFSET = 2_857_659_773  # actual dwSeekLength from the prior diagnostic

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
INVALID_HANDLE_VALUE = wt.HANDLE(-1).value
INVALID_SET_FILE_POINTER = 0xFFFFFFFF
FILE_BEGIN = 0
FILE_CURRENT = 1
FILE_END = 2

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

CreateFileW = kernel32.CreateFileW
CreateFileW.argtypes = [
    wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p,
    wt.DWORD, wt.DWORD, wt.HANDLE,
]
CreateFileW.restype = wt.HANDLE

# Two SetFilePointer prototypes -- with NULL and with non-NULL high pointer
SetFilePointer_NoHigh = kernel32.SetFilePointer
SetFilePointer_NoHigh.argtypes = [wt.HANDLE, wt.LONG, ctypes.c_void_p, wt.DWORD]
SetFilePointer_NoHigh.restype = wt.DWORD

SetFilePointer_WithHigh = kernel32.SetFilePointer
# Note: same function, different argtype binding -- we'll pass byref(LONG)

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wt.HANDLE]
CloseHandle.restype = wt.BOOL


def open_for_read(path: Path) -> int:
    h = CreateFileW(
        str(path),
        GENERIC_READ,
        FILE_SHARE_READ,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if h == INVALID_HANDLE_VALUE or h == 0 or h is None:
        err = ctypes.get_last_error()
        raise OSError(f"CreateFileW failed: GetLastError={err}")
    return h


def case_a_no_high(handle: int, offset: int) -> tuple[int, int]:
    """Mimic CFile::Seek(dwSeekLength, current) with NULL high pointer."""
    # Cast offset -> signed LONG (32-bit signed)
    if offset > 0x7FFFFFFF:
        signed = offset - 0x100000000
    else:
        signed = offset
    print(f"  Calling SetFilePointer(handle, lDistance={signed} (0x{offset & 0xFFFFFFFF:08X}), NULL, FILE_CURRENT)")
    result = SetFilePointer_NoHigh(handle, signed, None, FILE_CURRENT)
    last_err = ctypes.get_last_error()
    return result, last_err


def case_b_with_high(handle: int, offset: int) -> tuple[int, int, int]:
    """Mimic CFile::Seek((LONG)dwSeekLength, current, &lZero) -- the FIX."""
    high = wt.LONG(0)
    low_bits = offset & 0xFFFFFFFF  # the bit pattern (which a LONG cast preserves)
    # wt.LONG is signed 32-bit; passing the bit pattern as signed:
    if low_bits > 0x7FFFFFFF:
        signed_low = low_bits - 0x100000000
    else:
        signed_low = low_bits
    print(f"  Calling SetFilePointer(handle, lDistance={signed_low} (0x{low_bits:08X}), &lHigh=0, FILE_CURRENT)")
    result = SetFilePointer_WithHigh(handle, signed_low, ctypes.byref(high), FILE_CURRENT)
    last_err = ctypes.get_last_error()
    return result, high.value, last_err


def main() -> int:
    if not DB_PATH.exists():
        print(f"  [SKIP] {DB_PATH} does not exist")
        return 0

    file_size = DB_PATH.stat().st_size
    print(f"File: {DB_PATH}")
    print(f"Size: {file_size:,} bytes ({file_size / (1024**3):.2f} GB)")
    print(f"Seek target offset: +{SEEK_OFFSET:,} bytes from start\n")

    # --- Case A: pre-fix (NULL high pointer) ---
    print("=== Case A: PRE-FIX behavior (NULL high pointer) ===")
    print("    This matches the original DatabaseInfo.cpp Seek(dwSeekLength, current).")
    h = open_for_read(DB_PATH)
    try:
        # First seek to offset 0 (begin) so 'current' starts at 0
        SetFilePointer_NoHigh(h, 0, None, FILE_BEGIN)
        result, err = case_a_no_high(h, SEEK_OFFSET)
        if result == INVALID_SET_FILE_POINTER:
            print(f"  RESULT: FAILED (returned 0xFFFFFFFF). LastError={err}")
            print(f"  -> This is the bug: the >2GB DWORD wraps to negative LONG and")
            print(f"     SetFilePointer rejects the resulting offset.")
            case_a_failed = True
        else:
            print(f"  RESULT: returned {result:,} (low DWORD) -- but the high half is unknown.")
            # Re-query position by calling SetFilePointer with 0/current
            cur_low = SetFilePointer_NoHigh(h, 0, None, FILE_CURRENT)
            print(f"  Current position (low DWORD via NULL high): {cur_low:,}")
            case_a_failed = False
    finally:
        CloseHandle(h)
    print()

    # --- Case B: post-fix (high pointer = 0) ---
    print("=== Case B: POST-FIX behavior (high pointer = 0) ===")
    print("    This matches the fixed DatabaseInfo.cpp Seek((LONG)dwSeekLength, current, &lZero).")
    h = open_for_read(DB_PATH)
    try:
        high = wt.LONG(0)
        SetFilePointer_NoHigh(h, 0, ctypes.byref(high), FILE_BEGIN)
        result, ret_high, err = case_b_with_high(h, SEEK_OFFSET)
        if result == INVALID_SET_FILE_POINTER and err != 0:
            print(f"  RESULT: FAILED. LastError={err}")
            case_b_succeeded = False
        else:
            absolute = (ret_high << 32) | result
            print(f"  RESULT: low_dword=0x{result:08X} ({result:,}), high_dword=0x{ret_high:08X}")
            print(f"  Absolute file position after seek: {absolute:,} bytes")
            print(f"  Expected:                          {SEEK_OFFSET:,} bytes")
            case_b_succeeded = absolute == SEEK_OFFSET
    finally:
        CloseHandle(h)
    print()

    print("=== Summary ===")
    print(f"  Case A (pre-fix, NULL high)  : {'FAILED as expected' if case_a_failed else 'unexpectedly succeeded'}")
    print(f"  Case B (post-fix, high=0)    : {'SUCCEEDED' if case_b_succeeded else 'FAILED'}")

    if case_a_failed and case_b_succeeded:
        print("\n  [VERIFIED] The fix works: passing &lZero for the high pointer enables")
        print("             64-bit-style seeks for offsets in the 2-4 GB range.")
        return 0

    print("\n  [UNEXPECTED] Either pre-fix did not fail, or post-fix did not succeed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
