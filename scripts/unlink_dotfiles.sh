#!/bin/bash

FILES=(gitconfig vimrc tmux.conf)
echo "start unlink files(${FILES[@]})"

for file in ${FILES[@]}
do
    echo "unlink ${file}"
    unlink $HOME/.${file}
done


