# dotfiles
.gitconfig / .vimrc / .tmux.conf etc.....

# setup (create/unlink symlink to dotfiles)
$ source ~/dotfiles/scripts/setup_dotfiles.sh
$ source ~/dotfiles/scripts/unlink_dotfiles.sh

# Ubuntu IME settings
frame_work: fcitx5
input_engine: Mozc(JP), default(US)
$ sudo apt update && sudo apt install fcitx5 fcitx5-mozc fcitx5-configtool-qt
$ sudo apt purge ibus
$ reboot
setting "Input Method" and "Global options" inside the fcitx5-config

# vim prerequisite 
type: vim-gtk3
$ sudo apt-get update && sudo apt-get install vim-gtk3

# tmux
command_line_tool: xclip
$ sudo apt updat && sudo apt install tmux xclip
