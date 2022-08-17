#!/bin/sh

# This shell script is for making symlink 
# connecting home directory to dotfiles


echo "start setup dotfiles"

DOT_FILES=(.gitconfig .tmux.conf)
for file in ${DOT_FILES[@]}
do
	ln -s $HOME/dotfiles/$file $HOME/$file
done

echo "finish setup dotfiles"





