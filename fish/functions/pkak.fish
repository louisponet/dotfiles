function pkak
	
	set -l server_name (basename (pwd))
	set -l socket_file (/usr/bin/kak -l | grep $server_name)

	if [ "$socket_file" = "" ]        
	# Create new kakoune daemon for current dir
		/usr/bin/kak -d -s $server_name
	end

# and run kakoune (with any arguments passed to the script)
/usr/bin/kak -c $server_name $argv

end
