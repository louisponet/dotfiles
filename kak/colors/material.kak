evaluate-commands %sh{
    black_lighterer='rgb:383838'
    black_lighter='rgb:2D2D2D'
    black_light='rgb:1C1C1C'
    grey_dark='rgb:585858'
    grey_light='rgb:D8D8D8'
    magenta_dark='rgb:AB4642'
    magenta_light='rgb:AB4434'

    # i changed these for material
    green_dark='rgb:C3E88D'
    purple_dark='rgb:C792EA'
    cyan_light='rgb:89DDF3'
    orange_dark='rgb:F78C6A'
    orange_light='rgb:FFCB6B'

    # this ones are new
    normaltext='rgb:EEFFFF'
    background='rgb:263238' 

    ## code
    echo "
    	face global builtin default+b
    "
    ## markup
    echo "
       face global title blue
       face global header ${cyan_light}
       face global bold ${orange_light}
       face global italic ${orange_dark}
       face global mono ${green_dark}
       face global block ${orange_dark}
       face global link blue
       face global bullet ${magenta_light}
       face global list ${magenta_dark}
    "

    ## builtin
    echo "
       face global Default ${normaltext},${background}
       face global PrimarySelection white,blue
       face global SecondarySelection black,blue
       face global PrimaryCursor black,white
       face global SecondaryCursor black,white
       face global LineNumbers ${grey_light},${black_lighter}
       face global LineNumberCursor ${grey_light},rgb:282828+b
       face global MenuForeground ${grey_light},blue
       face global MenuBackground blue,${grey_light}
       face global MenuInfo ${cyan_light}
       face global Information ${black_light},${cyan_light}
       face global Error ${grey_light},${magenta_light}
       face global StatusLine ${grey_light},${black_lighterer}
       face global StatusLineMode ${orange_dark}
       face global StatusLineInfo ${cyan_light}
       face global StatusLineValue ${green_dark}
       face global StatusCursor ${black_lighterer},${cyan_light}
       face global Prompt ${black_light},${cyan_light}
       face global MatchingChar ${cyan_light},${black_light}+b
       face global BufferPadding ${cyan_light},${black_lighter}
    "
}

set-face global module    'rgb:C3E88D'
set-face global string    'rgb:C3E88D'
set-face global operator  'rgb:82AAFF'
set-face global function  'rgb:82AAFF'
set-face global attribute 'rgb:F78C6A'
set-face global value     'rgb:F78C6A'
set-face global meta      'rgb:FFCB6B'
set-face global type      'rgb:FFCB6B'
set-face global variable  'rgb:EEFFFF'
set-face global boolean   'rgb:F07178'
set-face global keyword   'rgb:C792EA'
set-face global comment   'rgb:4F6875'
set-face global end       'rgb:766291'
set-face global symbol    'rgb:89DDF3'
#set-face Default 'rgb:EEFFFF','rgb:263238' 

# julia code

#dd-highlighter shared/julia/code/ regex \b(true|false|nothing)\b 0:boolean
add-highlighter shared/julia/code/ regex (@\w+\s)|(\b([a-z]|[A-Z])\w+!?(?=\()) 0:function
add-highlighter shared/julia/code/ regex \bend\b 0:end
add-highlighter shared/julia/code/ regex (\.|:|~|`|!|\$|%|\^|&|\*|-|=|\+|\\|\||"|'|<|>|/) 0:symbol
add-highlighter shared/julia/code/ regex (0e-|(?<=[0-9])\.(?![a-z])(?![A-Z])(?!@)|\.(?=[0-9])|(?<=\[)end|end(?=\])) 0:value
# todo
# :as and :(
# $dstn in strings
# 'dstndstn'
# "dstnstdn"
