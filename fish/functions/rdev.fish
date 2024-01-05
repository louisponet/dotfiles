function rdev
	set commands (cat proj.files)
	set files (eval $commands[1])
	set -e commands[1]
	# echo $commands
	for v in $commands
		set files $files (eval $v)
	end

	kak $files -e "evaluate-commands %{
		buffer $files[1]
		ride
		}"
end
