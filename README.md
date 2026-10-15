# dotfiles
git(.gitconfig) , .vimrc , .tmux.conf , vscode(settings.json) etc.....

# setup (create symlink to dotfiles)
`$ source ~/dotfiles/scripts/setup_dotfiles.sh  `

# tear down (unlink symlink to dotfiles)
`$ source ~/dotfiles/scripts/unlink_dotfiles.sh  `

# Ubuntu IME settings
- software stacks
frame_work: fcitx5  
input_engine: Mozc(JP), default(US)
1. install packages
`$ sudo apt update && sudo apt install fcitx5 fcitx5-mozc fcitx5-configtool-qt  `
`$ sudo apt purge ibus  `
`$ reboot  `
2. setting "Input Method" and "Global options" inside the fcitx5-config  

# Git config syntax
- make sure the version is 2.36 or latter.
- make sure ~/.gitignore is deleated (which has higher priority than .config/git/*).
`sudo apt-add-repository ppa:git-core/ppa`
`sudo apt update && sudo apt install git`

# vim prerequisite 
- type: vim-gtk3  
`$ sudo apt-get update && sudo apt-get install vim-gtk3`

# tmux
- command_line_tool: xclip  
    - This is always needed when using tmux
`$ sudo apt updat && sudo apt install tmux xclip`
