#!/bin/bash

FILES=(vimrc tmux.conf)
echo "==== Start unlinking files(${FILES[@]})"
for file in ${FILES[@]}
do
    unlink $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${file}"
    else
        echo "[FAIL] ${file}"
    fi
done

# GIT_SETTINGS=(config gitconfig-han-github gitconfig-nachi-gitea)
GIT_SETTINGS=(git)
echo "==== Start unlinking (${GIT_SETTINGS[@]})"
for git_setting in ${GIT_SETTINGS[@]}
do
    # unlink $HOME/dotfiles/dotfiles/git/${git_setting} $HOME/.config/git/${git_setting}
    unlink $HOME/.config/${git_setting}
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${git_setting}"
    else
        echo "[FAIL] ${git_setting}"
    fi
done




VSCODE_SETTINGS=(settings.json keybindings.json)
echo "==== Start unlinking (${VSCODE_SETTINGS[@]})"
for vscode_setting in ${VSCODE_SETTINGS[@]}
do
    unlink $HOME/.config/Code/User/$vscode_setting
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${vscode_setting}"
    else
        echo "[FAIL] ${vscode_setting}"
    fi
done


VSCODE_SNIPPETS=(cpp.json cmake.json)
echo "==== Start unlinking (${VSCODE_SNIPPETS[@]})"
for vscode_snippet in ${VSCODE_SNIPPETS[@]}
do
    unlink $HOME/.config/Code/User/snippets/$vscode_snippet
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${vscode_snippet}"
    else
        echo "[FAIL] ${vscode_snippet}"
    fi
done


# Unlink the same Claude Code items that setup_dotfiles.sh linked.
CLAUDE_DOTFILES_DIR=$HOME/dotfiles/dotfiles/claude
echo "==== Start unlinking Claude Code settings (${CLAUDE_DOTFILES_DIR})"
for claude_source_path in "$CLAUDE_DOTFILES_DIR"/CLAUDE.md "$CLAUDE_DOTFILES_DIR"/settings.json "$CLAUDE_DOTFILES_DIR"/rules/*.md "$CLAUDE_DOTFILES_DIR"/skills/* "$CLAUDE_DOTFILES_DIR"/agents/*.md "$CLAUDE_DOTFILES_DIR"/output-styles/*.md
do
    claude_relative_path=${claude_source_path#"$CLAUDE_DOTFILES_DIR"/}
    unlink "$HOME/.claude/$claude_relative_path"
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${claude_relative_path}"
    else
        echo "[FAIL] ${claude_relative_path}"
    fi
done

