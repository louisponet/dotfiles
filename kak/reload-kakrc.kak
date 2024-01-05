# Reload kakrc and .kak when saving.
# Adds -allow-override to definitions (unless they seem to be python defs!)
# Removes shared highlighting
# Idea: remove all grouped hooks?

rmhooks global reloadKak
hook -group reloadKak global BufWritePost (.*kakrc|.*\.kak) %{
  rmhooks global kakrc
  decl -hidden str reload_file
  evaluate-commands %sh{
    tmp=$(mktemp /tmp/kak-source.XXXXXX)
    echo set buffer reload_file $tmp
  }
  write %opt{reload_file}
  nop %sh{
    cat $kak_opt_reload_file |
    grep 'add-highlighter shared/ regions -default \w\+ \w\+' |
    sed 's#.*add-highlighter shared/ regions -default \w\+ \(\w\+\).*#rmhl shared/\1#'
  }
  nop %sh{
    sed -i 's/^plug/#/' $kak_opt_reload_file

  }
  source %opt{reload_file}
  echo Reloaded %val{bufname}
  nop %sh{ rm $kak_opt_reload_file }
}

