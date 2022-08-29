#!/bin/bash

FILES=(gitconfig vimrc)
echo "start make symlink in (${HOME}) to dotfiles(${FILES})"

for file in ${FILES[@]}
do
    echo "file"
    ln -s $HOME/dotfiles/$file $HOME/.${file}
done







