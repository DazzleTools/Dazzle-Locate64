@echo off
REM ============================================================
REM  package_release.cmd
REM
REM  Cmd / batch shell wrapper around package_release.ps1 so the
REM  release packager works from a plain cmd prompt without users
REM  having to remember the powershell invocation.
REM
REM  Usage (cmd or batch):
REM      scripts\package_release.cmd
REM      scripts\package_release.cmd -Version "3.2-RC4-build11.8221"
REM      scripts\package_release.cmd -OutputDir "D:\releases"
REM
REM  All arguments are forwarded verbatim to the .ps1 script.
REM ============================================================

setlocal

REM Find a PowerShell host. Prefer pwsh (PS 7+) if present, fall
REM back to Windows PowerShell (powershell.exe, ships with Windows).
set "PS_EXE="
where pwsh.exe >nul 2>&1 && set "PS_EXE=pwsh.exe"
if not defined PS_EXE (
    where powershell.exe >nul 2>&1 && set "PS_EXE=powershell.exe"
)

if not defined PS_EXE (
    echo ERROR: Neither pwsh.exe nor powershell.exe was found on PATH.
    echo Install PowerShell 7 or run from a Windows machine with PowerShell installed.
    exit /b 127
)

REM %~dp0 is the directory of THIS .cmd, with trailing backslash.
set "PS1_PATH=%~dp0package_release.ps1"

if not exist "%PS1_PATH%" (
    echo ERROR: Script not found: %PS1_PATH%
    exit /b 1
)

REM -NoProfile        skip loading the user's PS profile
REM -ExecutionPolicy  bypass restricted-machine policy
REM -File             run the .ps1 (vs. -Command which interprets a string)
REM %*                forward every argument the user passed to this .cmd
"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%PS1_PATH%" %*

exit /b %ERRORLEVEL%
