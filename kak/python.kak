## http://julialang.org
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

# Detection
# ‾‾‾‾‾‾‾‾‾

require-module python
declare-user-mode python

hook global BufCreate .*\.(py) %{
    set-option buffer filetype python
	map -docstring 'python mode' buffer normal <ret> ':enter-user-mode python<ret>'

	map buffer python x ':python-start <ret>'      -docstring 'send python start command to repl'
	map buffer python h ':python-horizontal <ret>' -docstring 'open horizontal split with python'
	map buffer python v ':python-vertical <ret>'   -docstring 'open vertical split with python'
	# defaults to horizontal python
	map buffer python V ':python-restart-vertical   <ret>'   -docstring 'restart python vertically'
	map buffer python H ':python-restart-horizontal <ret>'   -docstring 'restart python horizontally'
	map buffer python s ':python-send-text <ret>'        -docstring 'send selection'
	map buffer python r ':python-send-text <ret>'        -docstring 'send selection'
	map buffer python p ':python-package-command <ret>'        -docstring 'execute a package command'
	map buffer python <space> %{<esc>gl<a-?>^\b<ret><a-;>BH?^end<ret><a-L>L<">ay| sed '/^$/d'<ret> :python-send-text<ret> <">apd /^\b<ret> /^\b<ret><esc>} -docstring 'send block'
	map buffer python <ret> "<esc>X :python-send-text <ret> j" -docstring 'send line'
	# runs all code between two #%% #%% markers
	map buffer python b %{<a-i>c#%%,#%%<ret><">ay| sed '/^$/d'<ret> :python-send-text<ret> <">apd/#%%<ret><esc> j} -docstring 'send comment-percent (#%%) block' 
}


#starting julia
def python -params ..  %{
    tmux-repl-vertical %sh{echo "python $@"}
    nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
 	nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
}

def python-vertical -params .. %{
    tmux-repl-horizontal %sh{echo "python $@"}
    nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
 	nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
}

def python-restart-vertical -params .. %{
	python-send-text 'exit()
'
	python-vertical %arg{@}
}

def python-restart-horizontal -params .. %{
	python-send-text 'exit()
'
	python-horizontal %arg{@}
}

def python-send-text -params .. %{
 	nop %sh{
	 	cmod=$(tmux display-message -t $kak_opt_tmux_repl_id -p -F '#{pane_in_mode}')
	 	if [ $cmod -eq "1" ]; then
	 		tmux send-keys -t $kak_opt_tmux_repl_id 'q' Enter
	 	fi
    }
    echo %arg{@}
 	repl-send-text %sh{printf "\b"}
    repl-send-text %arg{@}
}
