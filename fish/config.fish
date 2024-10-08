fish_vi_key_bindings
set -xg EDITOR kak
set -xg TERM xterm-256color

alias lsr 'ls $LS_OPTIONS -ltrFh'
alias tmuxls 'tmux list-sessions'
alias config '/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'
alias please sudo

set -xg PATH $HOME/.cargo/bin $HOME/.local/bin $HOME/bin $PATH 
set -xg PATH $HOME/Software/pcm/bin $PATH

## INTEL
set -xg LD_LIBRARY_PATH /opt/intel/compilers_and_libraries_2020.4.304/linux/compiler/lib/intel64_lin /opt/intel/compilers_and_libraries_2020.4.304/linux/mkl/lib/intel64_lin /home/ponet/Software/BTCS.Ipc/BTCS.Memory/c $LD_LIBRARY_PATH
set -xg PATH /home/ponet/Software/cargo-pgo/target/release /opt/intel/compilers_and_libraries/linux/bin/intel64 /opt/intel/compilers_and_libraries_2020.4.304/linux/mpi/intel64/bin $PATH

alias t tmuxinator
set -xg RUST_BACKTRACE 1
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
# eval /opt/miniconda3/bin/conda "shell.fish" "hook" $argv | source
# <<< conda initialize <<<
# starship init fish | source
zoxide init fish | source
set -xg RUSTC_WRAPPER sccache
set -xg RUST_LOG Info

if test -e $HOME/.config/fish/conf.d/local.fish
	source $HOME/.config/fish/conf.d/local.fish
end
if test -e $HOME/.config/fish/conf.d/local1.fish
	source $HOME/.config/fish/conf.d/local1.fish
end

set hook $(printf "{\"hook\": \"SSH\", \"value\": {\"socket_path\": \"~/.ssh/23581\", \"remote_shell\": \"%s\"}}" "$SHELL##*/" | command od -An -v -tx1 | command tr -d " \n")

set -xg ROCKSDB_LIB_DIR /lib
