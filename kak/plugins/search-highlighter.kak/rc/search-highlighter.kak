provide-module search-highlighter %{
  # Faces
  set-face global Search +u

  # Highlighters
  add-highlighter shared/search dynregex '%reg{/}' 0:Search

  # Commands
  # Enable
  define-command search-highlighter-enable -docstring 'Enable search-highlighter' %{
    search-highlighter-show
  }

  # Disable
  define-command search-highlighter-disable -docstring 'Disable search-highlighter' %{
    search-highlighter-hide
    remove-hooks global search-highlighter
  }

  # Show
  define-command -hidden search-highlighter-show %{
    add-highlighter global/search ref search

    # Hide on Escape
    hook -once -group search-highlighter global NormalKey '<esc>' %{
      search-highlighter-hide
    }
  }

  # Hide
  define-command -hidden search-highlighter-hide %{
    remove-highlighter global/search

    # Show when searching
    hook -once -group search-highlighter global NormalKey '[/?*nN]|<a-[/?*nN]>' %{
      search-highlighter-show
    }
  }
}
