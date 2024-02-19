def tmux-reset-ide-julia %{
    focus tools
    # nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 50 \/ 100)}

    focus jump
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 50 \/ 100)}
    focus client0
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 50 \/ 100)}
}

def tmux-reset-ide-c %{

    focus client0
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 33 \/ 100)}
    focus jump
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 33 \/ 100)}
    focus tools
    # nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 33 \/ 100)}
    focus client0
}
def tmux-reset-ide-cs %{

    focus jump
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 40 \/ 100)}
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    focus main
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 60 \/ 100)}
}

def tmux-reset-ide-rs %{

    focus jump
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 40 \/ 100)}
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    focus main
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 60 \/ 100)}
}

def tmux-reset-ide-rs-gdb %{

    focus jump
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 20 \/ 100)}
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    focus main
    # nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 60 \/ 100)}
}

def tmux-focus-julia %{
    focus client0
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 10 \/ 100)}
    nop %sh{tmux select-pane -D}
}
def tmux-focus-tools %{
    focus tools
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 80 \/ 100)}
}
def tmux-focus-hover %{
    focus lsp
    nop %sh{tmux resize-pane -y $(expr $(tmux display -p '#{window_height}') \* 80 \/ 100)}
    nop %sh{tmux resize-pane -x $(expr $(tmux display -p '#{window_width}') \* 80 \/ 100)}
}

