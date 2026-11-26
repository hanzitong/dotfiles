@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "DOTFILES=%USERPROFILE%\dotfiles\dotfiles"
set "GIT_CONFIG_DIR=%USERPROFILE%\.config"
set "VSCODE_DIR=%APPDATA%\Code\User"
set "CLAUDE_SOURCE=%DOTFILES%\claude"
set "CLAUDE_DIR=%USERPROFILE%\.claude"
set "FAILED=0"
set "UNLINK_DRY_RUN=0"

if defined XDG_CONFIG_HOME set "GIT_CONFIG_DIR=%XDG_CONFIG_HOME%"
if defined CLAUDE_CONFIG_DIR set "CLAUDE_DIR=%CLAUDE_CONFIG_DIR%"
if /I "%~1"=="--dry-run" set "UNLINK_DRY_RUN=1"

echo ==== Vim and tmux ====
call :unlink "%DOTFILES%\vimrc" "%USERPROFILE%\_vimrc"
call :unlink "%DOTFILES%\vimrc" "%USERPROFILE%\.vimrc"
call :unlink "%DOTFILES%\tmux.conf" "%USERPROFILE%\.tmux.conf"

echo ==== Git ====
call :unlink "%DOTFILES%\git" "%GIT_CONFIG_DIR%\git"

echo ==== VSCode settings ====
for %%F in (settings.json keybindings.json) do (
    call :unlink "%DOTFILES%\vscode\%%F" "%VSCODE_DIR%\%%F"
)

echo ==== VSCode snippets ====
for %%F in (cpp.json cmake.json) do (
    call :unlink "%DOTFILES%\vscode\snippets\%%F" "%VSCODE_DIR%\snippets\%%F"
)

echo ==== Claude Code ====
for %%F in (CLAUDE.md settings.json) do (
    call :unlink "%CLAUDE_SOURCE%\%%F" "%CLAUDE_DIR%\%%F"
)

rem Enumerate destinations so links to removed source files can also be cleaned.
for %%D in (rules agents output-styles) do (
    for %%F in ("%CLAUDE_DIR%\%%D\*.md") do (
        call :unlink "%CLAUDE_SOURCE%\%%D\%%~nxF" "%%~fF"
    )
)

for /D %%D in ("%CLAUDE_DIR%\skills\*") do (
    call :unlink "%CLAUDE_SOURCE%\skills\%%~nxD" "%%~fD"
)
for %%F in ("%CLAUDE_DIR%\skills\*") do (
    call :unlink "%CLAUDE_SOURCE%\skills\%%~nxF" "%%~fF"
)

for %%F in ("%CLAUDE_DIR%\hooks\*.py") do (
    call :unlink "%CLAUDE_SOURCE%\hooks\%%~nxF" "%%~fF"
)
call :unlink "%CLAUDE_SOURCE%\hooks\README.md" "%CLAUDE_DIR%\hooks\README.md"

echo ==== Finished ====
exit /b %FAILED%

:unlink
rem Arguments: expected source, destination.
rem Pass paths through environment variables instead of inserting them into PS code.
set "UNLINK_SOURCE=%~1"
set "UNLINK_DEST=%~2"

rem PowerShell is used to check the exact link type and target.
rem FileInfo.Delete / DirectoryInfo.Delete remove the link without recursion.
powershell.exe -NoProfile -NonInteractive -Command ^
    "$ErrorActionPreference = 'Stop'; try {" ^
    "$dest = $env:UNLINK_DEST; $parent = Split-Path -LiteralPath $dest; $name = [IO.Path]::GetFileName($dest);" ^
    "if (-not (Test-Path -LiteralPath $parent -PathType Container)) { Write-Host ('[SKIP] Not found: ' + $dest); exit 0 };" ^
    "$item = Get-ChildItem -LiteralPath $parent -Force | Where-Object { $_.Name -ieq $name } | Select-Object -First 1;" ^
    "if ($null -eq $item) { Write-Host ('[SKIP] Not found: ' + $dest); exit 0 };" ^
    "if ($item.LinkType -ne 'SymbolicLink') { Write-Host ('[SKIP] Not a symbolic link: ' + $dest); exit 0 };" ^
    "$targets = @($item.Target); if ($targets.Count -ne 1 -or $targets[0] -ine $env:UNLINK_SOURCE) { Write-Host ('[SKIP] Different or unreadable target: ' + $dest); exit 0 };" ^
    "if ($env:UNLINK_DRY_RUN -eq '1') { Write-Host ('[DRY-RUN] Would unlink: ' + $dest); exit 0 };" ^
    "$item.Delete(); Write-Host ('[SUCCESS] Unlinked: ' + $dest); exit 0" ^
    "} catch { Write-Host ('[FAIL] ' + $env:UNLINK_DEST + ': ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 set "FAILED=1"
exit /b 0

