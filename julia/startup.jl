# Disable updating registry on `add` (still runs on `up`), as it is slow
# using JuliaSyntax
# JuliaSyntax.enable_in_core!()
using Pkg: Pkg
Pkg.UPDATED_REGISTRY_THIS_SESSION[] = true
# using AbbreviatedStackTraces

# use more colors for displaying Pkg conflicts
if isdefined(Pkg.Resolve, :CONFLICT_COLORS)
    append!(Pkg.Resolve.CONFLICT_COLORS,  [21:51; 55:119; 124:142; 160:184; 196:220])
end

using Revise
using Crayons
using OhMyREPL
import OhMyREPL: Passes.SyntaxHighlighter
scheme = SyntaxHighlighter.ColorScheme()
SyntaxHighlighter.comment!(scheme, Crayon(foreground = 0x006eb5ff))
SyntaxHighlighter.function_def!(scheme, Crayon(foreground = 0x00ff748b))
SyntaxHighlighter.call!(scheme, Crayon(foreground = 0x006eb5ff))
SyntaxHighlighter.string!(scheme, Crayon(foreground = 0x009f65cf))
SyntaxHighlighter.symbol!(scheme, Crayon(foreground = 0x0045d4e8))
SyntaxHighlighter.keyword!(scheme, Crayon(foreground = 0x00d1be2a))
SyntaxHighlighter.op!(scheme, Crayon(foreground = 0x00d1be2a))
SyntaxHighlighter.macro!(scheme, Crayon(foreground = 0x00ff748b))
SyntaxHighlighter.number!(scheme, Crayon(foreground = 0x00d350de))
SyntaxHighlighter.add!("qiita", scheme)
colorscheme!("qiita")
enable_autocomplete_brackets(false)

if Base.isinteractive() &&
   (local REPL = get(Base.loaded_modules, Base.PkgId(Base.UUID("3fa0cd96-eef1-5676-8a61-b3b8758bbffb"), "REPL"), nothing); REPL !== nothing)

    # Exit Julia with :q, restart with :r
    # pushfirst!(REPL.repl_ast_transforms, function(ast::Union{Expr,Nothing})
    #     function toplevel_quotenode(ast, s)
    #         return (Meta.isexpr(ast, :toplevel, 2) && ast.args[2] === QuoteNode(s)) ||
    #                (Meta.isexpr(ast, :toplevel) && any(x -> toplevel_quotenode(x, s), ast.args))
    #     end
    #     if toplevel_quotenode(ast, :q)
    #         exit()
    #     elseif toplevel_quotenode(ast, :r)
    #         argv = Base.julia_cmd().exec
    #         opts = Base.JLOptions()
    #         if opts.project != C_NULL
    #             push!(argv, "--project=$(unsafe_string(opts.project))")
    #         end
    #         if opts.nthreads != 0
    #             push!(argv, "--threads=$(opts.nthreads)")
    #         end
    #         # @ccall execv(argv[1]::Cstring, argv::Ref{Cstring})::Cint
    #         ccall(:execv, Cint, (Cstring, Ref{Cstring}), argv[1], argv)
    #     end
    #     return ast
    # end)

    # Automatically load tooling on demand:
    # - BenchmarkTools.jl when encountering @btime or @benchmark
    # - Cthulhu.jl when encountering @descend(_code_(typed|warntype))
    # - Debugger.jl when encountering @enter or @run
    # - Profile.jl when encountering @profile
    # - ProfileView.jl when encountering @profview
    local tooling_dict = Dict{Symbol,Vector{Symbol}}(
        :BenchmarkTools => Symbol.(["@btime", "@benchmark"]),
        :Cthulhu        => Symbol.(["@descend", "@descend_code_typed", "@descend_code_warntype"]),
        :Debugger       => Symbol.(["@enter", "@run"]),
        :Profile        => Symbol.(["@profile"]),
        :ProfileView    => Symbol.(["@profview"]),
        :TimerOutputs   => Symbol.(["@timeit"]),
    )
    pushfirst!(REPL.repl_ast_transforms, function(ast::Union{Expr,Nothing})
        function contains_macro(ast, m)
            return ast isa Expr && (
                (Meta.isexpr(ast, :macrocall) && ast.args[1] === m) ||
                any(x -> contains_macro(x, m), ast.args)
            )
        end
        for (mod, macros) in tooling_dict
            if any(contains_macro(ast, s) for s in macros) && !isdefined(Main, mod)
                @info "Loading $mod ..."
                try
                    Core.eval(Main, :(using $mod))
                catch err
                    @info "Failed to automatically load $mod" exception=err
                end
            end
        end
        return ast
    end)

end



# try
#     import Term: install_term_stacktrace, install_term_logger, install_term_repr
#     install_term_stacktrace()
#     install_term_logger()
#     install_term_repr()
# catch e
#     @warn "Error initializing term" exception=(e, catch_backtrace())
# end
