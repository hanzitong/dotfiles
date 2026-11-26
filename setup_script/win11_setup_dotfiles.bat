

@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "DOTFILES=%USERPROFILE%\dotfiles\dotfiles"
set "GIT_CONFIG_DIR=%USERPROFILE%\.config"
set "VSCODE_DIR=%APPDATA%\Code\User"
set "CLAUDE_SOURCE=%DOTFILES%\claude"
set "CLAUDE_DIR=%USERPROFILE%\.claude"
set "FAILED=0"

if defined XDG_CONFIG_HOME set "GIT_CONFIG_DIR=%XDG_CONFIG_HOME%"
if defined CLAUDE_CONFIG_DIR set "CLAUDE_DIR=%CLAUDE_CONFIG_DIR%"

if not exist "%DOTFILES%\." (
    echo [FAIL] Dotfiles directory not found: "%DOTFILES%"
    exit /b 1
)

echo ==== Vim and tmux ====
rem Native Windows Vim and Git Bash Vim use different file names.
call :link "%DOTFILES%\vimrc" "%USERPROFILE%\_vimrc"
call :link "%DOTFILES%\vimrc" "%USERPROFILE%\.vimrc"
call :link "%DOTFILES%\tmux.conf" "%USERPROFILE%\.tmux.conf"

echo ==== Git ====
call :link "%DOTFILES%\git" "%GIT_CONFIG_DIR%\git" /D

echo ==== VSCode settings ====
for %%F in (settings.json keybindings.json) do (
    call :link "%DOTFILES%\vscode\%%F" "%VSCODE_DIR%\%%F"
)

echo ==== VSCode snippets ====
for %%F in (cpp.json cmake.json) do (
    call :link "%DOTFILES%\vscode\snippets\%%F" "%VSCODE_DIR%\snippets\%%F"
)

echo ==== Claude Code ====
rem Link individual items, not the whole .claude directory.
for %%F in (CLAUDE.md settings.json) do (
    call :link "%CLAUDE_SOURCE%\%%F" "%CLAUDE_DIR%\%%F"
)

for %%D in (rules agents output-styles) do (
    for %%F in ("%CLAUDE_SOURCE%\%%D\*.md") do (
        if exist "%%~fF" call :link "%%~fF" "%CLAUDE_DIR%\%%D\%%~nxF"
    )
)

for /D %%D in ("%CLAUDE_SOURCE%\skills\*") do (
    call :link "%%~fD" "%CLAUDE_DIR%\skills\%%~nxD" /D
)
for %%F in ("%CLAUDE_SOURCE%\skills\*") do (
    if exist "%%~fF" if not exist "%%~fF\." call :link "%%~fF" "%CLAUDE_DIR%\skills\%%~nxF"
)

for %%F in ("%CLAUDE_SOURCE%\hooks\*.py" "%CLAUDE_SOURCE%\hooks\README.md") do (
    if exist "%%~fF" call :link "%%~fF" "%CLAUDE_DIR%\hooks\%%~nxF"
)

echo ==== Finished ====
exit /b %FAILED%

:link
rem Arguments: source, destination, optional /D for a directory.
if not exist "%~1" (
    echo [FAIL] Source not found: "%~1"
    set "FAILED=1"
    exit /b 1
)

if exist "%~2" (
    echo [SKIP] Destination already exists: "%~2"
    exit /b 0
)

for %%P in ("%~2") do (
    if not exist "%%~dpP." mkdir "%%~dpP."
)

mklink %~3 "%~2" "%~1" >nul
if errorlevel 1 (
    echo [FAIL] "%~2"
    set "FAILED=1"
    exit /b 1
)

echo [SUCCESS] "%~2"
exit /b 0






