#!/bin/bash

FILES=(vimrc tmux.conf)
echo "==== Start making symlink in (${HOME}) to dotfiles(${FILES[@]})"
for file in ${FILES[@]}
do
    ln -s $HOME/dotfiles/dotfiles/$file $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${file}"
    else
        echo "[FAIL] ${file}"
    fi
done


# GIT_SETTINGS=(config gitconfig-han-github gitconfig-nachi-gitea)
GIT_SETTINGS=(git)
echo "==== Start making symlink of (${GIT_SETTINGS[@]})"
for git_setting in ${GIT_SETTINGS[@]}
do
    if [ ! -d $HOME/.config/ ]; then
        # mkdir -p $HOME/.config/git/
        mkdir -p $HOME/.config/
    fi

    # ln -s $HOME/dotfiles/dotfiles/git/${git_setting} $HOME/.config/git/${git_setting}
    ln -sT $HOME/dotfiles/dotfiles/${git_setting} $HOME/.config/${git_setting}
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${git_setting}"
    else
        echo "[FAIL] ${git_setting}"
    fi
done


VSCODE_SETTINGS=(settings.json keybindings.json)
echo "==== Start making symlink of (${VSCODE_SETTINGS[@]})"
for vscode_setting in ${VSCODE_SETTINGS[@]}
do
    if [ ! -d $HOME/.config/Code/User ]; then
        mkdir -p $HOME/.config/Code/User
    fi

    ln -s $HOME/dotfiles/dotfiles/vscode/$vscode_setting $HOME/.config/Code/User/$vscode_setting
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${vscode_setting}"
    else
        echo "[FAIL] ${vscode_setting}"
    fi
done


VSCODE_SNIPPETS=(cpp.json cmake.json)
echo "==== Start making symlink of (${VSCODE_SNIPPETS[@]})"
for vscode_snippet in ${VSCODE_SNIPPETS[@]}
do
    if [ ! -d $HOME/.config/Code/User/snippets ]; then
        mkdir -p $HOME/.config/Code/User/snippets
    fi

    ln -s $HOME/dotfiles/dotfiles/vscode/snippets/$vscode_snippet $HOME/.config/Code/User/snippets/$vscode_snippet
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] ${vscode_snippet}"
    else
        echo "[FAIL] ${vscode_snippet}"
    fi
done

