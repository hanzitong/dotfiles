#!/bin/bash

FILES=(gitconfig vimrc tmux.conf)
echo "start making symlink in (${HOME}) to dotfiles(${FILES[@]})"
for file in ${FILES[@]}
do
    ln -s $HOME/dotfiles/dotfiles/$file $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "${file} success"
    else
        echo "${file} fail"
    fi
done


VSCODE_SETTINGS=(settings.json keybindings.json)
echo "start making symlink of (${VSCODE_SETTINGS[@]})"
for vscode_setting in ${VSCODE_SETTINGS[@]}
do
    ln -s $HOME/dotfiles/dotfiles/vscode/$vscode_setting $HOME/.config/Code/User/$vscode_setting
    if [ $? -eq 0 ]; then
        echo "${vscode_setting} success"
    else
        echo "${vscode_setting} fail"
    fi
done


VSCODE_SNIPPETS=(cpp.json)
echo "Start making symlink of (${VSCODE_SNIPPETS[@]})"
for vscode_snippet in ${VSCODE_SNIPPETS[@]}
do
    ln -s $HOME/dotfiles/dotfiles/vscode/snippets/$vscode $HOME/.config/Code/User/snippets/$vscode_snippet
    if [ $? -eq 0 ]; then
        echo "${vscode_snippet} success"
    else
        echo "${vscode_snippet} fail"
    fi
done

