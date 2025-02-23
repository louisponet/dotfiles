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
		set files (fd -e .rs) (fd Cargo.toml)

	end
	set -xg KAK_LSP_FORCE_PROJECT_ROOT (pwd)
	kak $files -e "evaluate-commands %{
		buffer $files[1]
		ride
		}"
end
