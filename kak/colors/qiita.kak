# Solarized Dark

evaluate-commands %sh{
	base03='rgb:1B2529'
	base02='rgb:073642'
	base01='rgb:586e75'
	base00='rgb:657b83'
	base0='rgb:E3E3E3'
	base1='rgb:93a1a1'
	base2='rgb:eee8d5'
	base3='rgb:fdf6e3'
	yellow='rgb:e0c810'
	rusty='rgb:ad9ea2'
	lightyellow='rgb:8f727b'
	orange='rgb:cb4b16'
	red='rgb:FF748B'
	magenta='rgb:d350de'
	violet='rgb:9F65CF'
    lightblue='rgb:ffbffe'	
	blue='rgb:6EB5FF'
	cyan='rgb:45D4e8'
	green='rgb:00f76b'
	lightgreen='rgb:63ffa6'
	darkgreen='rgb:009640'
	gray='rgb:26343B'
	darkblue='rgb:395E6B'

   echo "
        # code
        face global end                ${yellow}+d
        face global value              ${magenta}
        face global type               ${cyan}
        face global variable           ${base0},${base03}
        face global module             ${rusty}
        face global meta               ${rusty}
        face global function           ${blue}
        face global functiondecl       ${red}
        face global string             ${violet}
        face global keyword            ${yellow}
        face global operator           ${yellow}
        face global attribute          ${red}
        face global comment            ${base01}
        face global builtin            ${yellow}
        face global symbol             ${yellow}
        face global scopedecl          ${red}
        face global member             ${lightblue}
        # markup
        face global title              ${blue}+b
        face global header             ${blue}
        face global bold               ${base0}+b
        face global italic             ${base0}+i
        face global mono               ${base1}
        face global block              ${cyan}
        face global link               ${base1}
        face global bullet             ${yellow}
        face global list               ${green}
        face global cursorline         ${base0},${gray}
        face global Search   ${base0},${darkblue}
        face global PrimarySelectionSearch   ${base0},${blue}
        face global PrimarySelectionDefault ${base0},${darkblue}

        # builtin
        face global Default            ${base0},${base03}
        face global PrimarySelection   ${base0},${darkblue}
        face global SecondarySelection ${base01},${base1}
        face global PrimaryCursor      ${base03},${green}+fg
        face global SecondaryCursor    ${base03},${darkgreen}+fg
        face global PrimaryCursorEol   ${base03},${green}+fg
        face global SecondaryCursorEol ${base03},${darkgreen}+fg
        face global LineNumbers        ${base01},${base03}
        face global LineNumberCursor   ${base01},${base03}
        face global LineNumbersWrapped ${base01},${base03}
        face global MenuForeground     ${base03},${yellow}
        face global MenuBackground     ${base1},${base02}
        face global MenuInfo           ${base01}
        face global Information        ${base02},${base1}
        face global Error              ${red},default+b
        face global StatusLine         ${base1},${base02}+b
        face global StatusLineMode     ${orange}
        face global StatusLineInfo     ${cyan}
        face global StatusLineValue    ${green}
        face global StatusCursor       ${base00},${base3}
        face global Prompt             ${yellow}+b
        face global MatchingChar       ${cyan},${darkgreen}+b
        face global BufferPadding      ${base01},${base03}
        face global Whitespace         ${base01}+f
    "
}
