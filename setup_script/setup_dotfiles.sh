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







