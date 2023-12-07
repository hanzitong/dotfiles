#!/bin/bash

FILES=(gitconfig vimrc tmux.conf)
echo "start unlink files(${FILES[@]})"

for file in ${FILES[@]}
do
    unlink $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "unlink ${file}"
    else
        echo "failed to unlink ${file}"
    fi
done


