function fkill
	if [ "$UID" != "0" ]
set pid (ps -f -u $UID | sed 1d | fzf -m | awk '{print $2}')
else
set pid (ps -ef | sed 1d | fzf -m | awk '{print $2}')
end
if [ "x$pid" != "x" ]
echo $pid | xargs kill -s 9
end
end
