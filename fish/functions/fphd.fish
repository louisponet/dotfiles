function fphd
    set -l dir (find $HOME/Documents/PhD -type d -print 2> /dev/null | fzf-tmux --query="$argv[1]" --select-1)
    cd $dir
end
