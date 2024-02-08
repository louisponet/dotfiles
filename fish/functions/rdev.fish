function rdev
	if test -f proj.files
		set commands (cat proj.files)
		set files (eval $commands[1])
		set -e commands[1]
		# echo $commands
		for v in $commands
			set files $files (eval $v)
		end
	else
		if command -v fd &> /dev/null
			set files (fd .rs)
		else
			set files (find -name  "*.rs")
		end
	end
	kak $files -e "evaluate-commands %{
		buffer $files[1]
		ride
		}"
end
