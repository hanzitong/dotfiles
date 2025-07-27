#!/bin/bash

FILES=(gitconfig vimrc tmux.conf)
echo "start unlink files(${FILES[@]})"

for file in ${FILES[@]}
do
    unlink $HOME/.${file}
    if [ $? -eq 0 ]; then
        echo "succeded to unlink ${file}"
    else
        echo "failed to unlink ${file}"
    fi
done


VSCODE_FILES=(settings.json keybindings.json)
echo "start make symlink of (${VSCODE_FILES[@]})"

for vscode_file in ${VSCODE_FILES[@]}
do
    unlink $HOME/.config/Code/User/$vscode_file
    if [ $? -eq 0 ]; then
        echo "${vscode_file} success"
    else
        echo "${vscode_file} fail"
    fi
done


# SETTINGSJSON=(settings.json)
# echo "start unlink (${SETTINGSJSON[@]})"

# for json in ${SETTINGSJSON[@]}
# do
#     unlink $HOME/.config/Code/User/settings.json
#     if [ $? -eq 0 ]; then
#         echo "succeded to unlink ${json}"
#     else
#         echo "failed to unlink ${json}"
#     fi
# done



