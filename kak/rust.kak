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
    set-option global makecmd 'export RUST_LOG_STYLE=always && export RUST_LOG=DEBUG && export CARGO_TERM_COLOR=always && cargo'
    set-option global make_error_pattern "error(?:\[E\d+\])?: (?:[^\n]+)?\n\s+-->\s+([^:\n]+):(\d+):(\d+)"
    declare-option regex make_error_line_pattern "\s+-->\s+([^:\n]+):(\d+):(\d+)"
    set-option global gdb_program 'rust-gdb'
    map buffer normal <C-F5> ': rs-start-gdb<ret>'


    define-command -hidden -override make-jump %{
        evaluate-commands -save-regs / %{
            try %{
                execute-keys gl<a-?> "Entering directory" <ret><a-:>
                # Try to parse the error into capture groups, failing on absolute paths
                execute-keys s "Entering directory [`']([^']+)'.*\n([^:/][^:]*):(\d+):(?:(\d+):)?([^\n]+)\z" <ret>l
                set-option buffer make_current_error_line %val{cursor_line}
                make-open-error "%reg{1}/%reg{2}" "%reg{3}" "%reg{4}" "%reg{5}"
            } catch %{
                set-register / %opt{make_error_line_pattern}
                execute-keys <a-h><a-l> s<ret>l
                set-option buffer make_current_error_line %val{cursor_line}
                make-open-error "%reg{1}" "%reg{2}" "%reg{3}" "%reg{4}"
            }
        }
    }
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

