#!/bin/sh

dotfiles_root=$(cd $(dirname $0)/.. && pwd)

# make link connecting each content under home directory
cd ${dotfiles_root}/dotfiles
for file in .*; do
	ln -s ${pwd}/${file} ${HOME}
done



