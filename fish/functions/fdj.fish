function fdj
    set -l dir (find $HOME/.julia/dev $HOME/.julia/environments -path '*/.git*' -prune -o -path '*/deps*' -prune -o \
                 -type d -print 2> /dev/null | fzf-tmux --query="$argv[1]" --select-1)
    cd $dir
end
