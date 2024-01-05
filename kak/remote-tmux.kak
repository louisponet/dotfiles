def remote-tmux-repl-vertical -params 1..2 -docstring '
remote-tmux-repl-vertical <remote-server>[<tmux-session-name>]: Create a new vertical tmux repl terminal on the remote-server, if no name is supplied it will attach/create a session with name kak_tmux_repl.' %{
	evaluate-commands %sh{
		if [ $# -eq 2 ]; then
			printf "%s\n" "tmux-repl-vertical 'ssh $1 -t tmux new-session -A -s $2'"
		else
			printf "%s\n" "tmux-repl-vertical 'ssh $1 -t tmux new-session -A -s kak_tmux_repl'"
		fi
	}
	nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
}

def remote-tmux-repl-horizontal -params 1..2 -docstring '
remote-tmux-repl-horizontal <remote-server>[<tmux-session-name>]: Create a new horizontal tmux repl terminal on the remote-server, if no name is supplied it will attach/create a session with name kak_tmux_repl.' %{
	evaluate-commands %sh{
		if [ $# -eq 2 ]; then
			printf "%s\n" "tmux-repl-horizontal 'ssh $1 -t tmux new-session -A -s $2'"
		else
			printf "%s\n" "tmux-repl-horizontal 'ssh $1 -t tmux new-session -A -s kak_tmux_repl'"
		fi
	}
	nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
}
