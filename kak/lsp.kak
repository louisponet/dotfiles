eval %sh{kak-lsp --kakoune -s $kak_session}

# uncomment to enable debugging
eval %sh{echo ${kak_opt_lsp_cmd} >> /tmp/kak-lsp.log}
set global lsp_cmd "kak-lsp -s %val{session} -vvv --log /tmp/kak-lsp.log"

# 
set global lsp_diagnostic_line_error_sign '║'
set global lsp_diagnostic_line_warning_sign '┊'
set global lsp_hover_max_lines 40
define-command ne -docstring 'go to next error/warning from lsp' %{ lsp-find-error --include-warnings }
define-command pe -docstring 'go to previous error/warning from lsp' %{ lsp-find-error --previous --include-warnings }
define-command ee -docstring 'go to current error/warning from lsp' %{ lsp-find-error --include-warnings; lsp-find-error --previous --include-warnings }

define-command lsp-restart -docstring 'restart lsp server' %{ lsp-stop; lsp-start }

hook global WinSetOption filetype=(c|cpp|cc|rust|javascript|typescript|julia|fortran|c-sharp|cucumber) %{
    set-option window lsp_hover_anchor false
    # lsp-auto-hover-enable
    lsp-auto-signature-help-enable
    echo -debug "Enabling LSP for filtetype %opt{filetype}"
    map global normal <c-l> %{:enter-user-mode lsp<ret>} -docstring "LSP mode"
    map global normal Q ':lsp-hover<ret>'
    map global insert <a-tab> '<a-;>:try lsp-snippets-select-next-placeholders catch %{ execute-keys -with-hooks <lt><tab> }<ret>' -docstring 'Select next snippet placeholder'
    map global object a '<a-semicolon>lsp-object<ret>' -docstring 'LSP any symbol'
    map global object <a-a> '<a-semicolon>lsp-object<ret>' -docstring 'LSP any symbol'
    map global object e '<a-semicolon>lsp-object Function Method<ret>' -docstring 'LSP function or method'
    map global object k '<a-semicolon>lsp-object Class Interface Struct<ret>' -docstring 'LSP class interface or struct'
    map global object d '<a-semicolon>lsp-diagnostic-object --include-warnings<ret>' -docstring 'LSP errors and warnings'
    map global object D '<a-semicolon>lsp-diagnostic-object<ret>' -docstring 'LSP errors'


    map global lsp o '<esc>: lsp-workspace-symbol-incr<ret>: focus tools<ret>' -docstring 'search project symbols'
    map global lsp i '<esc>: lsp-implementation<ret>: focus tools<ret>' -docstring 'go to implementation'
    map global lsp r '<esc>: lsp-references<ret>: focus tools<ret>'              -docstring 'list symbol references'
    map global lsp S '<esc>: lsp-document-symbol<ret>: focus tools<ret>'         -docstring 'list document symbols'
    map global normal <c-k> '<esc>: lsp-selection-range<ret>'
    map global lsp-selection-range <c-k> '<esc>: lsp-selection-range-select up<ret>'
    lsp-enable-window
}
hook global WinSetOption filetype=(python) %{
    # set-option global lsp_config %{
    #         [language.python.settings._]
    #  	"pyls.configurationSources" = ["flake8"]
    # }
    set-option window lsp_hover_anchor false
    # lsp-auto-hover-enable
    set-option global lsp_server_configuration pyls.plugins.pycodestyle.ignore=["E501","E128","E221"]
    set-option global lsp_server_configuration pyls.configurationSources=["flake8"]
    echo -debug "Enabling LSP for filtetype %opt{filetype}"
    map global user l ":enter-user-mode lsp<ret>"
    map global normal <c-q> ":enter-user-mode lsp<ret>o"
    lsp-enable-window
}

hook global WinSetOption filetype=(c|cpp) %{
  hook window -group semantic-tokens BufReload .* lsp-semantic-tokens
  hook window -group semantic-tokens NormalIdle .* lsp-semantic-tokens
  hook window -group semantic-tokens InsertIdle .* lsp-semantic-tokens
add-highlighter shared/cpp/code/ regex (|~|`|!|\$|%|\^|&|\*|-|=|\+|\\|\||"|'|<|>|/) 0:symbol
  hook -once -always window WinSetOption filetype=.* %{
    remove-hooks window semantic-tokens
  }
}
hook global WinSetOption filetype=c-sharp %{
  hook window -group semantic-tokens BufReload .* lsp-semantic-tokens
  hook window -group semantic-tokens NormalIdle .* lsp-semantic-tokens
  hook window -group semantic-tokens InsertIdle .* lsp-semantic-tokens
  hook -once -always window WinSetOption filetype=.* %{
    remove-hooks window semantic-tokens
  }
}

hook global KakEnd .* lsp-exit
