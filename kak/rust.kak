def rs-start-gdb %{
    prompt 'bin: ' %{
        evaluate-commands -client main %{
            nop %sh{cargo build --bin ${kak_val_text}}
            gdb-session-new "target/debug/%val{text}"
        }
        gdb-enable-autojump
        tmux-reset-ide-rs-gdb
        execute-keys ':gdb-start '
    }
}

hook global WinSetOption filetype=rust %{
    set-option buffer makecmd 'cargo'
    set-option global gdb_program 'rust-gdb'
    map buffer normal <C-F5> ': rs-start-gdb<ret>'
}

def ride %{
    rename-client jump
    vnew %{
        rename-client main
        set global jumpclient jump
        evaluate-commands -client jump %{
        	hnew %{
            	rename-client tools
                set global toolsclient tools
        	}
        }
        tmux-reset-ide-rs
    }
    map global user <space> ": tmux-reset-ide-rs<ret>" -docstring 'reset ide windows'
}

