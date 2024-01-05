## http://julialang.org
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

# Detection
# ‾‾‾‾‾‾‾‾‾

require-module julia
declare-user-mode julia

hook global BufCreate .*\.(jl) %{
    set-option buffer filetype julia
	map -docstring 'julia mode' buffer normal <ret> ':enter-user-mode julia<ret>'

	map buffer julia x ': julia-start <ret>'      -docstring 'send julia start command to repl'
	map buffer julia h ': julia-horizontal <ret>' -docstring 'open horizontal split with julia'
	map buffer julia v ': julia-vertical <ret>'   -docstring 'open vertical split with julia'
	# defaults to horizontal julia
	map buffer julia V ': julia-restart-vertical   <ret>'   -docstring 'restart julia vertically'
	map buffer julia H ': julia-restart-horizontal <ret>'   -docstring 'restart julia horizontally'
	map buffer julia s ': julia-send-text <ret>'        -docstring 'send selection'
	map buffer julia r ': julia-send-remote-text <ret>' -docstring 'send selection to remote'
	map buffer julia p ': julia-package-command <ret>'  -docstring 'execute a package command'
	map buffer julia <space> %{<esc>gl<a-?>^\b<ret><a-;>BH?^end<ret><a-L>L: julia-send-text <ret>j} -docstring 'send block'
	map buffer julia <ret> %{<esc>giGlL: julia-send-text <ret>j} -docstring 'send line'
	# runs all code between two #%% #%% markers
	# map buffer julia b %{<a-i>c#%%,#%%<ret><">ay| sed '/^$/d'<ret>: julia-send-text<ret> <">apd/#%%<ret><esc> j} -docstring 'send comment-percent (#%%) block' 
	map buffer julia b %{<a-i>c#%%,#%%<ret>: julia-send-text<ret>j} -docstring 'send comment-percent (#%%) block' 
}


# Initialization
# ‾‾‾‾‾‾‾‾‾‾‾‾‾‾
define-command -hidden julia-indent-on-char %{
    evaluate-commands -no-hooks -draft -itersel %{
        try %{ execute-keys -draft 'B<">jy'}
	    execute-keys %sh{ eval set -- "$kak_reg_j"
	    	if [ $1 = "end" ] || [ $1 = "else" ] || [ $1 = "catch" ] || [ $1 = "finally" ]; then
	    		echo "<lt>"
	    	fi
	    }
    }
}

define-command -hidden julia-indent-on-new-line %{
    evaluate-commands -draft -itersel %{
        # copy '#' comment prefix and following white spaces
        # try %{ execute-keys -draft k <a-x> s ^\h*#\h* <ret> y jgh P }
        # preserve previous line indent
        try %{ execute-keys -draft \; K <a-&> }
        # cleanup trailing whitespaces from previous line
        try %{ execute-keys -draft k x s \h+$ <ret> d }
        # indent after line ending with :
        try %{ execute-keys -draft k x <a-k>^(@|\w|\.|\s|=)*\b(if|else|elseif|while|for|begin|quote|try|catch|function|macro|ccall|finally|module|do|baremodule|struct)\b <ret> j <a-gt> }
    }
}

# new user mode

#starting julia
def julia-horizontal -params ..  %{
    tmux-repl-vertical %sh{echo "julia $@"}
    nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
 	nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    repl-send-text 'Base.active_repl.options.auto_indent=false
'
}

def julia-vertical -params .. %{
    tmux-repl-horizontal %sh{echo "julia $@"}
    nop %sh{tmux select-pane -t $kak_client_env_TMUX_PANE}
 	nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    repl-send-text 'Base.active_repl.options.auto_indent=false
'
}

def julia-start -params .. %{
	julia-send-text %sh{
		echo "julia $@
	Base.active_repl.options.auto_indent=false
 "
	}
}
def julia-restart-vertical -params .. %{
	julia-send-text 'exit()
'
	julia-vertical %arg{@}
}

def julia-restart-horizontal -params .. %{
	julia-send-text 'exit()
'
	julia-horizontal %arg{@}
}

def julia-send-text -params .. %{
 	nop %sh{
	 	cmod=$(tmux display-message -t $kak_opt_tmux_repl_id -p -F '#{pane_in_mode}')
	 	if [ $cmod -eq "1" ]; then
	 		tmux send-keys -t $kak_opt_tmux_repl_id 'q' Enter
	 	fi
    }
    echo %arg{@}
 	repl-send-text %sh{printf "\b"}
    repl-send-text %arg{@}
 	repl-send-text %sh{printf "\b"}
}

def julia-send-remote-text -params .. %{
 	nop %sh{
	 	cmod=$(tmux display-message -t $kak_opt_tmux_repl_id -p -F '#{pane_in_mode}')
	 	if [ $cmod -eq "1" ]; then
	 		tmux send-keys -t $kak_opt_tmux_repl_id 'q' Enter
	 	fi
    }
    echo %arg{@}
 	repl-send-text %sh{printf "\b>"}
    repl-send-text %arg{@}
 	repl-send-text %sh{printf "\b"}
}

def julia-package-command %{
 	prompt pkg: %{julia-send-text "]%val{text}
"}
}

# Highlighters
# ‾‾‾‾‾‾‾‾‾‾‾‾
remove-highlighter shared/julia/code/
add-highlighter shared/julia/code default-region group

add-highlighter shared/julia/code/ regex (?<!:)(?!\[)(?<!\[)\bend\b 0:end

add-highlighter shared/julia/code/ regex \b(true|false|nothing)\b 0:value
add-highlighter shared/julia/code/ regex \b(ComplexF32|ComplexF64)\b 0:type
add-highlighter shared/julia/code/ regex (\.|:|~|`|!|\$|%|\^|&|\*|-|=|\+|\\|\||"|'|<|>|/) 0:symbol
add-highlighter shared/julia/code/ regex (?<=\[)\s*(?<e>end)|(?<d>end)(\s|[0-9]|-|\+|\*|/)*(?=\]) e:value d:value
add-highlighter shared/julia/code/ regex ((\b0(x|X)[0-9a-fA-F](_?[0-9a-fA-F])*)|(\b0o[0-7](_?[0-7])*)|(\b0b[0-1](_?[0-1])*)|((\b[0-9](_?[0-9])*\.?(_?[0-9]*))|(\.[0-9](_?[0-9])*))([eE][+-]?[0-9](_?[0-9])*)?(f0)?(im\b)?|\bInf(32)?\b|\bNaN(32)?\b) 0:value
add-highlighter shared/julia/code/ regex \b(if|else|elseif|while|for|begin|quote|try|catch|return|function|macro|ccall|finally|typealias|break|continue|module|using|import|export|bitstype|do|in|baremodule|struct|mutable|where)\b 0:keyword
add-highlighter shared/julia/code/ regex \b(abstract\stype)\b 0:keyword
add-highlighter shared/julia/code/ regex \b(local|global|const|let)\b 0:scopedecl

add-highlighter shared/julia/code/ regex (?:::|<:|>:)\s*((\w|\.)*) 1:type

add-highlighter shared/julia/code/ regex (?:type|struct)\s*(\w+) 1:Default


add-highlighter shared/julia/code/ regex (?<![0-9])(?<![:<])(?<![^a-zA-Z]:)(?!end)(:\w+) 0:type
add-highlighter shared/julia/code/ regex (\w+)((?:\{(?:[^\{\}]|\{(?:[^\{\}]|\{[^\{\}]*\})*\})*\})) 0:type

add-highlighter shared/julia/code/ regex (?<!function\s)((@\w+\s)|(\b(\w+!*(:?\.)?)(?:\{(?:[^\{\}]|\{(?:[^\{\}]|\{[^\{\}]*\})*\})*\})?(?=\())) 4:function


add-highlighter shared/julia/code/ regex ((function|macro)\s*)(\b[\w\.!]*)(?:\{(?:[^\{\}]|\{(?:[^\{\}]|\{[^\{\}]*\})*\})*\})?(?=\()) 3:functiondecl
add-highlighter shared/julia/code/ regex (\b[\w\.!]*)(?:\{(?:[^\{\}]|\{(?:[^\{\}]|\{[^\{\}]*\})*\})*\})?.?\([^\)]*\)(::[^\s]+)?(\s*\bwhere\b\s*[^\s]*((?:\{(?:[^\{\}]|\{(?:[^\{\}]|\{[^\{\}]*\})*\})*\}))*)?\s*?=(?!=)  1:functiondecl


# add-highlighter shared/julia/code/ regex (::|<:)\s*(\w+(\{[(?:\{??[^\{]*?\})|)) 2:type

#add such that s and <ret> do the same depending on whether a bigger than 1 selection is done
hook global WinSetOption filetype=julia %{
    # add-highlighter window/julia ref julia
    hook window InsertChar [dehy] -group julia-indent julia-indent-on-char
    hook window InsertChar \n -group julia-indent julia-indent-on-new-line
    # cleanup trailing whitespaces on current line insert end
    hook window ModeChange insert:.* -group julia-trim-indent %{ try %{ execute-keys -draft \; <a-x> s ^\h+$ <ret> d }} 
    hook -always -once window WinSetOption filetype=.* %{  remove-hooks window julia-.+
    	remove-highlighter window/julia
    }
}
