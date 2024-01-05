require-module python

hook global BufCreate .*\.(py) %{
    set-option buffer filetype python
}


# Initialization
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾
# define-command -hidden julia-indent-on-char %{
#     evaluate-commands -no-hooks -draft -itersel %{
#         # align middle and end structures to start
#         try %{ execute-keys -draft <a-x> <a-k> ^ \h * (else|elsif) $ <ret> <a-\;> <a-?> ^ \h * (if)                                                       <ret> s \A | \z <ret> ) <a-&> }
#         try %{ execute-keys -draft <a-x> <a-k> ^ \h * (catch|finally)     $ <ret> <a-\;> <a-?> ^ \h * (try)                                                    <ret> s \A | \z <ret> ) <a-&> }
#         try %{ execute-keys -draft <a-x> <a-k> ^ \h * (end)        $ <ret> <a-\;> <a-?> ^ \h * (begin|quote|function|do|for|if|module|while) <ret> s \A | \z <ret> ) <a-&> }
#     }
# }


#starting julia
def verdi-horizontal %{
    tmux-repl-vertical "conda activate aiida-dev && ipython --no-autoindent"

    verdi-send-text "from aiida import load_profile
"
    verdi-send-text "load_profile()
"
    nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
 	nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
}

def verdi-vertical %{
    tmux-repl-horizontal "conda activate aiida-dev && ipython --no-autoindent"

    verdi-send-text "from aiida import load_profile
"
    verdi-send-text "load_profile()
"
    nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
}
def verdi-restart-vertical -params .. %{
	verdi-send-text 'exit()
'
	verdi-vertical %arg{@}
}

def verdi-restart-horizontal -params .. %{
	verdi-send-text 'exit()
'
	verdi-horizontal %arg{@}
}

def verdi-send-text -params .. %{
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

# Highlighters
# ‾‾‾‾‾‾‾‾‾‾‾‾
#add such that s and <ret> do the same depending on whether a bigger than 1 selection is done
hook -group verdi global WinSetOption filetype=python %{
    # add-highlighter window/julia ref julia
    # cleanup trailing whitespaces on current line insert end
	declare-user-mode verdi
	map -docstring 'verdi mode' global normal <ret> ':enter-user-mode verdi<ret>'

	map global verdi h ':verdi-horizontal <ret>' -docstring 'open horizontal split with verdi'
	map global verdi v ':verdi-vertical <ret>'   -docstring 'open vertical split with verdi'
	# defaults to horizontal verdi
	map global verdi V ':verdi-restart-vertical   <ret>'   -docstring 'restart verdi vertically'
	map global verdi H ':verdi-restart-horizontal <ret>'   -docstring 'restart verdi horizontally'
	map global verdi s ':verdi-send-text <ret>'        -docstring 'send selection'
	map global verdi <ret> "<esc>X :verdi-send-text <ret> j" -docstring 'send line'
	# runs all code between two #%% #%% markers
	map global verdi b %{<a-i>c#%%,#%%<ret><">ay| sed '/^$/d'<ret> :verdi-send-text<ret> <">apd/#%%<ret><esc> j} -docstring 'send comment-percent (#%%) block' 
    hook -once -always window WinSetOption filetype=.* %{  remove-hooks window verdi-.+
    }
}
