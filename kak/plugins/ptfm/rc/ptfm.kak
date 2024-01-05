declare-option str ptfm_win_id 999999
declare-option -hidden str ptfm_src %val{source}

define-command -override ptfm-sway %{
	eval %sh{

        # try to move to the ptfm window
    	win_id=$(swaymsg -t get_tree | jq '.. | (.nodes? // empty)[] | select(.focused==true).id')
        swaymsg "[con_id=$kak_opt_ptfm_win_id] focus" > /dev/null
        sleep 0.1
        # check if the ptfm window exists already
        test $(swaymsg -t get_tree | jq '.. | (.nodes? // empty)[] | select(.focused==true).id') = $kak_opt_ptfm_win_id > /dev/null 

        # otherwise, create the ptfm window
    	if [ $? -ne 0 ]; then
            setsid ${kak_opt_termcmd} "sh -c 'sleep 0.1; \
                 $(dirname $kak_opt_ptfm_src)/../.venv/bin/ptfm -k \
                 $kak_session:$kak_client:$win_id -p'"  < /dev/null > /dev/null 2>&1 &
        fi
	}
}


define-command -override ptfm-tmux %{
    eval %sh{
        pane_id="$TMUX_PANE"
        printf "echo -debug pane_id=\"%%{${pane_id}}\"\n"
        tmux has-session -t $kak_opt_ptfm_win_id && tmux select-pane -t $kak_opt_ptfm_win_id || \
        tmux split-window -h -b -p 25 $(dirname $kak_opt_ptfm_src)/../.venv/bin/ptfm -k \
                 "$kak_session:$kak_client:$pane_id"
    }
}
