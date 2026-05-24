#!/bin/bash

FILES=(gitconfig vimrc tmux.conf)
echo "Start unlinking files(${FILES[@]})"
for file in ${FILES[@]}
do
    unlink $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "succeded to unlink ${file}"
    else
        echo "failed to unlink ${file}"
    fi
done


VSCODE_SETTINGS=(settings.json keybindings.json)
echo "Start unlinking (${VSCODE_SETTINGS[@]})"
for vscode_setting in ${VSCODE_SETTINGS[@]}
do
    unlink $HOME/.config/Code/User/$vscode_setting
    if [ $? -eq 0 ]; then
        echo "${vscode_setting} success"
    else
        echo "${vscode_setting} fail"
    fi
done


VSCODE_SNIPPETS=(cpp.json)
echo "Start unlinking (${VSCODE_SNIPPETS[@]})"
for vscode_snippet in ${VSCODE_SNIPPETS[@]}
do
    unlink $HOME/.config/Code/User/snippets/$vscode_snippet
    if [ $? -eq 0 ]; then
        echo "${vscode_snippet} success"
    else
        echo "${vscode_snippet} fail"
    fi
done

