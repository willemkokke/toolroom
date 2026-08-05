# Typing & the stubs

toolroom is typed the way the bridge works: the runtime accepts
anything the installed tool accepts, and the stubs make the common
calls autocomplete without ever forbidding the uncommon ones.

## Two rules keep the stubs honest

- **Every verb ends in `**flags: Any`.** A stub can *suggest* flags —
  read from the tool itself — but never forbid one. When a tool grows
  a flag, the bridge already speaks it; the stub merely hasn't heard
  of it yet.
- **Unknown verbs fall through.** Attribute access resolves through
  `Tool.__getattr__`, so nothing the runtime accepts is a type error.

Stub drift therefore degrades a hint, never a run.

## Where the stubs come from

One generated file per curated tool, read from the installed binaries
on Linux, Windows, and macOS — each header records the tool version it
was read from. The generator, the option-event history it maintains,
and the refresh workflow currently live in
[footman's repository](https://github.com/willemkokke/footman) and are
moving here with the machinery.

## The building surface

Every generated class is generic over what a call returns. A running
handle answers in `Result`; `.argv` re-parameterises the same class
over `Argv`, so a *built* call keeps the same flag checking as a run:

<!-- example: fragment -->
```python
from toolroom import git

sha_cmd = git.rev_parse.argv("HEAD")  # Argv, same completions, same checks
```

## Checked everywhere

The package ships `py.typed`, the hand stub declares the whole public
surface (`Tool`, `Argv`, `Result`, `ToolError`, `off`, the curated
handles), and type-checking a toolroom consumer requires nothing but
toolroom — the stubs never import footman.
