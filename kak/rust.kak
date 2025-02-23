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

hook global WinSetOption -once filetype=rust %{
    set-option global makecmd 'export RUST_LOG_STYLE=always && export RUST_LOG=DEBUG && export CARGO_TERM_COLOR=always && cargo'
    set-option global make_error_pattern "error(?:\[E\d+\])?: (?:[^\n]+)?\n\s+-->\s+([^:\n]+):(\d+):(\d+)"
    declare-option regex make_error_line_pattern "\s+-->\s+([^:\n]+):(\d+):(\d+)"
    set-option global gdb_program 'rust-gdb'
    map global normal <C-F5> ': rs-start-gdb<ret>'

    declare-user-mode make

    map global normal <a-m> ': enter-user-mode make<ret>'
    map global make b ': make build<ret>' -docstring 'build'
    map global make c ': make clippy --all-features --no-deps -- -D warnings<ret>' -docstring 'clippy'
    map global make t ': make test<ret>' -docstring 'test'
    map global make f ': make +nightly-2024-10-01 fmt<ret>' -docstring 'fmt'

    define-command -hidden -override make-jump %{
        evaluate-commands -save-regs a/ %{
            evaluate-commands -draft %{
                execute-keys ,
                set-register / %opt{make_error_line_pattern}
                execute-keys <a-h><a-l>s<ret>l
                set-option buffer jump_current_line %val{cursor_line}
                set-register a "%reg{1}" "%reg{2}" "%reg{3}" "%reg{4}"
            }
            make-open-error %reg{a}
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

