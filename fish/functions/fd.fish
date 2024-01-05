function fd
    set -l dir (find -path '*/\.*' -prune \
                    -o -type d -print 2> /dev/null | fzf-tmux --query="$argv[1]")
    cd $dir
end

