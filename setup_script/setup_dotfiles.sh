#!/bin/bash

FILES=(gitconfig vimrc tmux.conf)
echo "start make symlink in (${HOME}) to dotfiles(${FILES[@]})"

for file in ${FILES[@]}
do
    ln -s $HOME/dotfiles/dotfiles/$file $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "${file} success"
    else
        echo "${file} fail"
    fi
done


VSCODE_FILES=(settings.json keybindings.json)
echo "start make symlink of (${VSCODE_FILES[@]})"

for vscode_file in ${VSCODE_FILES[@]}
do
    ln -s $HOME/dotfiles/dotfiles/$vscode_file $HOME/.config/Code/User/$vscode_file
    if [ $? -eq 0 ]; then
        echo "${vscode_file} success"
    else
        echo "${vscode_file} fail"
    fi
done







