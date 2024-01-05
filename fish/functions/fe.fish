function fe
	set -l files (fzf-tmux --query="$argv" --multi --select-1)
if count $files
$EDITOR "$files"
end
end
